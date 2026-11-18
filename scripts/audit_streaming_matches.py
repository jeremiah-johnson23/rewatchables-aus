#!/usr/bin/env python3
"""
Streaming match audit for The Rewatchables AU.

For every episode, re-queries JustWatch AU and grades how confident we are that
the JustWatch title it lands on is the *same film* the episode is about, then
diffs the fresh subscription offers against what's stored.

Match grades
    verified  exact title + year within 1 + director matches
    likely    exact title + year within 1, director unavailable to compare
    suspect   something disagrees (partial title, year off, director mismatch,
              or another candidate with the same title/year exists)
    missing   no acceptable JustWatch candidate

Streaming is only overwritten for verified/likely matches (with --apply).
Suspect/missing entries keep their stored data and are listed for hand review.

Writes audit/streaming-audit.json and audit/streaming-audit.md.

Usage:
    python scripts/audit_streaming_matches.py            # report only
    python scripts/audit_streaming_matches.py --apply    # report + update episodes.json
    python scripts/audit_streaming_matches.py --ids heat,the-town
"""

import argparse
import json
import re
import time
import unicodedata
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).parent.parent
EPISODES_PATH = ROOT / "src" / "data" / "episodes.json"
AUDIT_DIR = ROOT / "audit"
JUSTWATCH_GRAPHQL = "https://apis.justwatch.com/graphql"

PROVIDER_MAP = {
    8: "netflix", 1796: "netflix",
    21: "stan",
    119: "primeVideo", 9: "primeVideo", 2100: "primeVideo",
    337: "disneyPlus",
    385: "binge",
    531: "paramount",
    350: "appleTv",
    1899: "hboMax",
}
RENT_BUY_PROVIDERS = {
    2: "Apple TV", 3: "Google Play", 10: "Amazon", 192: "YouTube", 68: "Microsoft Store",
}
SERVICES = ["netflix", "stan", "primeVideo", "disneyPlus", "binge", "paramount", "appleTv", "hboMax"]

# Richest query first; fall back if JustWatch's schema rejects a field.
QUERY_VARIANTS = [
    ("full", """
      content(country: $country, language: "en") {
        title originalReleaseYear fullPath
        externalIds { imdbId tmdbId }
        credits(role: DIRECTOR) { name }
      }"""),
    ("ids", """
      content(country: $country, language: "en") {
        title originalReleaseYear fullPath
        externalIds { imdbId tmdbId }
      }"""),
    ("basic", """
      content(country: $country, language: "en") {
        title originalReleaseYear fullPath
      }"""),
]
QUERY_TEMPLATE = """
query Search($country: Country!, $filter: TitleFilter!, $first: Int!) {
  popularTitles(country: $country, filter: $filter, first: $first) {
    edges { node {
      id objectId objectType
      %s
      offers(country: $country, platform: WEB) {
        monetizationType
        package { packageId clearName }
      }
    } }
  }
}"""

_query_level = 0  # index into QUERY_VARIANTS that JustWatch accepts


NUM_WORDS = {w: str(i) for i, w in enumerate(
    "zero one two three four five six seven eight nine ten eleven twelve".split())}


def norm(s):
    s = unicodedata.normalize("NFKD", s or "").encode("ascii", "ignore").decode()
    s = s.lower().replace("&", "and")
    s = re.sub(r"\(live show\)|\(live\)", "", s)
    s = re.sub(r"[^a-z0-9 ]+", " ", s)
    s = re.sub(r"^(the|a|an) ", "", s.strip())
    s = " ".join(NUM_WORDS.get(w, w) for w in s.split())
    return re.sub(r"\s+", " ", s).strip()


def surname(name):
    parts = [w for w in norm(name).split() if w not in ("jr", "sr", "ii", "iii", "brothers")]
    return parts[-1] if parts else ""


def jw_search(query, first=8):
    global _query_level
    while True:
        name, fields = QUERY_VARIANTS[_query_level]
        payload = json.dumps({
            "query": QUERY_TEMPLATE % fields,
            "variables": {"country": "AU", "filter": {"searchQuery": query}, "first": first},
        }).encode()
        req = urllib.request.Request(JUSTWATCH_GRAPHQL, data=payload, headers={
            "Content-Type": "application/json",
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)",
        })
        t0 = time.time()
        for attempt in range(4):
            try:
                with urllib.request.urlopen(req, timeout=10) as r:
                    data = json.loads(r.read().decode())
                break
            except urllib.error.HTTPError as e:
                if e.code == 429:
                    wait = int(e.headers.get("Retry-After") or 0) or 30 * (attempt + 1)
                    print(f"    429 - backing off {wait}s")
                    time.sleep(min(wait, 180))
                    if attempt == 3:
                        return []
                    continue
                # GraphQL validation errors come back as HTTP 400 with a JSON body
                try:
                    data = json.loads(e.read().decode())
                    if data.get("errors"):
                        break
                except Exception:
                    pass
                if attempt == 3:
                    print(f"    ! request failed: {e}")
                    return []
                time.sleep(2 * (attempt + 1))
            except Exception as e:  # network hiccup / 429
                if attempt == 3:
                    print(f"    ! request failed: {e}")
                    return []
                time.sleep(2 * (attempt + 1))
        if time.time() - t0 > 5:
            print(f"    slow request {time.time() - t0:.1f}s for '{query}'")
        if data.get("errors") and _query_level < len(QUERY_VARIANTS) - 1:
            print(f"    ! query level '{name}' rejected: {data['errors'][0].get('message','')[:120]}")
            _query_level += 1
            continue
        edges = ((data.get("data") or {}).get("popularTitles") or {}).get("edges") or []
        return [e["node"] for e in edges if e.get("node", {}).get("objectType") == "MOVIE"]


def parse_offers(node):
    s = {k: False for k in SERVICES}
    rb = set()
    for o in node.get("offers") or []:
        pid = (o.get("package") or {}).get("packageId")
        m = o.get("monetizationType")
        if m in ("FLATRATE", "FREE", "ADS") and pid in PROVIDER_MAP:
            s[PROVIDER_MAP[pid]] = True
        elif m in ("RENT", "BUY") and pid in RENT_BUY_PROVIDERS:
            rb.add(RENT_BUY_PROVIDERS[pid])
    s["rentBuy"] = sorted(rb)
    return s


# Episodes whose JustWatch AU title differs from the episode title
TITLE_ALIASES = {
    "victory": "Escape to Victory",          # US title vs JustWatch AU title
    "a-few-good-re-men": "A Few Good Men",   # live re-cover episode
}

# JustWatch search can't surface these; their streaming is checked by hand.
# They're reported separately in the audit so they don't read as new problems.
HAND_CHECKED = {
    "memento": "JW search only returns Memento Mori - check https://www.justwatch.com/au/movie/memento",
    "the-sure-thing-1985": "Not listed on JustWatch AU",
}


def grade(ep, candidates):
    """Pick the best candidate and return (node, grade, reasons)."""
    want_t = norm(TITLE_ALIASES.get(ep.get("id"), ep["title"]))
    want_y = ep.get("year")
    want_dir = {surname(d) for d in re.split(r",| and |/", ep.get("director") or "") if d.strip()}

    scored = []
    for n in candidates:
        c = n.get("content") or {}
        t, y = norm(c.get("title")), c.get("originalReleaseYear")
        score, why = 0, []
        raw = c.get("title") or ""
        base = norm(raw.split(":")[0])
        want_base = norm(TITLE_ALIASES.get(ep.get("id"), ep["title"]).split(":")[0])
        if t == want_t:
            score += 100
        elif want_t in (base,) or t == want_base:
            score += 90; why.append(f"subtitle variant '{raw}'")
        elif want_t and (want_t in t or t in want_t):
            score += 40; why.append(f"partial title '{c.get('title')}'")
        else:
            score -= 50; why.append(f"different title '{c.get('title')}'")
        if want_y and y:
            dy = abs(y - want_y)
            if dy <= 1:
                score += 50
            else:
                score -= 30 * min(dy, 5); why.append(f"year {y} vs {want_y}")
        dirs = c.get("credits")
        dir_state = "n/a"
        if dirs is not None and want_dir:
            got = {surname(d.get("name")) for d in dirs if d.get("name")}
            if got and got & want_dir:
                score += 40; dir_state = "match"
            elif got:
                score -= 60; dir_state = "mismatch"
                why.append("director " + ", ".join(d["name"] for d in dirs[:2]))
        scored.append((score, n, why, dir_state, t, y))

    if not scored:
        return None, "missing", ["no movie results"], None
    scored.sort(key=lambda x: -x[0])
    best_score, node, why, dir_state, t, y = scored[0]
    if best_score < 60:
        return node, "missing", why or ["low score"], dir_state

    # Ambiguity: another distinct title with same name & close year
    rivals = [s for s in scored[1:] if s[4] == t and s[5] and y and abs(s[5] - y) <= 1
              and s[1].get("id") != node.get("id")]
    if rivals and dir_state != "match":
        why = why + [f"{len(rivals)} other JustWatch title(s) with same name/year"]

    # A subtitle variant with matching year + director is the same film
    if dir_state == "match" and why and all(w.startswith("subtitle variant") for w in why):
        why = []
    exact = (t == want_t or dir_state == "match") and (not want_y or not y or abs(y - want_y) <= 1)
    if exact and dir_state == "match" and not why:
        g = "verified"
    elif exact and dir_state == "n/a" and not why:
        g = "likely"
    else:
        g = "suspect"
    return node, g, why, dir_state


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    ap.add_argument("--ids")
    ap.add_argument("--empty", action="store_true",
                    help="only episodes with no streaming data yet (weekly new-episode mode, no report)")
    ap.add_argument("--dry", action="store_true", help="print results, write nothing")
    args = ap.parse_args()

    data = json.loads(EPISODES_PATH.read_text())
    eps = data["episodes"]
    if args.ids:
        wanted = set(args.ids.split(","))
        eps = [e for e in eps if e["id"] in wanted]

    if args.empty:
        eps = [e for e in eps if not any((e.get("streaming") or {}).get(k) for k in SERVICES)
               and not (e.get("streaming") or {}).get("rentBuy")]
        print(f"{len(eps)} episode(s) with no streaming data")
    today = time.strftime("%Y-%m-%d")
    rows = []
    for i, ep in enumerate(eps, 1):
        title, year = ep["title"], ep.get("year")
        clean = re.sub(r"\s*\((live show|live)\)\s*", "", TITLE_ALIASES.get(ep["id"], title), flags=re.I)
        cands, seen = [], set()
        for q in ([f"{clean} {year}"] if year else []) + [clean]:
            for n in jw_search(q):
                if n.get("id") not in seen:
                    seen.add(n.get("id")); cands.append(n)
            time.sleep(1.0)
            node, g, why, dir_state = grade(ep, cands)
            if g == "verified":
                break  # no need for the broader title-only query

        if ep["id"] in HAND_CHECKED and g not in ("verified", "likely"):
            g, why = "hand", [HAND_CHECKED[ep["id"]]]
        old = ep.get("streaming") or {}
        row = {
            "id": ep["id"], "title": title, "year": year, "director": ep.get("director"),
            "grade": g, "reasons": why, "director_check": dir_state,
            "old": {k: bool(old.get(k)) for k in SERVICES},
            "oldRentBuy": old.get("rentBuy") or [],
        }
        if node:
            c = node.get("content") or {}
            row["jw"] = {
                "id": node.get("id"), "title": c.get("title"), "year": c.get("originalReleaseYear"),
                "url": "https://www.justwatch.com" + (c.get("fullPath") or ""),
                "imdb": (c.get("externalIds") or {}).get("imdbId"),
                "directors": [d.get("name") for d in (c.get("credits") or [])],
            }
            new = parse_offers(node)
            row["new"] = {k: new[k] for k in SERVICES}
            row["newRentBuy"] = new["rentBuy"]
            row["added"] = [k for k in SERVICES if new[k] and not row["old"][k]]
            row["removed"] = [k for k in SERVICES if row["old"][k] and not new[k]]
            if args.apply and g in ("verified", "likely"):
                ep["streaming"] = new
                ep["lastStreamingCheck"] = today
                row["applied"] = True
        rows.append(row)
        flag = "" if g in ("verified", "likely") else "  <-- " + "; ".join(why)
        print(f"[{i}/{len(eps)}] {g:8s} {title} ({year}){flag}")

    if args.empty:
        for r in rows:
            if r["grade"] not in ("verified", "likely"):
                print(f"::warning::Streaming not applied for {r['title']} ({r['year']}): {r['grade']} - {'; '.join(r['reasons'])}")
        if args.apply:
            EPISODES_PATH.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n")
        return
    if args.dry:
        print(f"query level: {QUERY_VARIANTS[_query_level][0]}")
        for r in rows:
            print(json.dumps({k: r.get(k) for k in ("title", "grade", "reasons", "jw", "new")}))
        return
    AUDIT_DIR.mkdir(exist_ok=True)
    (AUDIT_DIR / "streaming-audit.json").write_text(json.dumps(
        {"date": today, "queryLevel": QUERY_VARIANTS[_query_level][0], "rows": rows}, indent=2, ensure_ascii=False))
    write_markdown(rows, today)

    if args.apply:
        EPISODES_PATH.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n")
        print(f"Applied fresh streaming to {sum(1 for r in rows if r.get('applied'))} episodes")


def svc_list(d):
    return ", ".join(k for k in SERVICES if d.get(k)) or "none"


def write_markdown(rows, today):
    from collections import Counter
    g = Counter(r["grade"] for r in rows)
    trusted = [r for r in rows if r["grade"] in ("verified", "likely")]
    changed = [r for r in trusted if r.get("added") or r.get("removed")]
    L = [f"# Streaming match audit — {today}", "",
         f"JustWatch query level: `{QUERY_VARIANTS[_query_level][0]}`", "",
         "| Grade | Count |", "|---|---|"]
    for k in ("verified", "likely", "suspect", "missing", "hand"):
        L.append(f"| {k} | {g.get(k, 0)} |")
    L += ["", f"Of {len(trusted)} trusted matches, {len(changed)} had stored subscription data that was out of date "
          f"({len(trusted) - len(changed)} unchanged).", ""]
    add, rem = Counter(), Counter()
    for r in changed:
        add.update(r["added"]); rem.update(r["removed"])
    L += ["| Service | Added | Removed |", "|---|---|---|"]
    for s in SERVICES:
        L.append(f"| {s} | {add.get(s, 0)} | {rem.get(s, 0)} |")
    L += ["", "## Needs review (suspect / missing)", ""]
    for r in rows:
        if r["grade"] in ("suspect", "missing"):
            jw = r.get("jw") or {}
            L.append(f"- **{r['title']}** ({r['year']}, {r['director']}) — {r['grade']}: {'; '.join(r['reasons'])}. "
                     f"JW → {jw.get('title')} ({jw.get('year')}) {jw.get('url','')}. Stored: {svc_list(r['old'])}")
    L += ["", "## Checked by hand (known)", ""]
    for r in rows:
        if r["grade"] == "hand":
            L.append(f"- **{r['title']}** ({r['year']}) — {r['reasons'][0]}. Stored: {svc_list(r['old'])}")
    L += ["", "## Changes applied", ""]
    for r in changed:
        L.append(f"- {r['title']} ({r['year']}): +{', '.join(r['added']) or '—'} / -{', '.join(r['removed']) or '—'}")
    (AUDIT_DIR / "streaming-audit.md").write_text("\n".join(L) + "\n")


if __name__ == "__main__":
    main()
