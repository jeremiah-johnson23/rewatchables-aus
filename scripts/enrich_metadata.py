#!/usr/bin/env python3
"""
Enrich skeleton episodes with metadata from Wikidata.

Free, no signup, no API key. Data is CC0.
Fills in: year, director, genres, studio for episodes missing that data.
"""

import json
import re
import time
import urllib.request
import urllib.parse
from pathlib import Path

EPISODES_PATH = Path(__file__).parent.parent / "src" / "data" / "episodes.json"
WIKIPEDIA_API = "https://en.wikipedia.org/w/api.php"
WIKIDATA_SPARQL = "https://query.wikidata.org/sparql"

# Wikimedia requires a descriptive User-Agent with contact info.
USER_AGENT = "RewatchablesAU/1.0 (https://rewatchables.au; simon@reflive.com)"

# Map Wikidata genre tokens to our genre names. We split multi-word genres
# (e.g. "crime drama film" → ["crime","drama","film"]) and match each token.
GENRE_MAP = {
    "action": "Action",
    "adventure": "Adventure",
    "animated": "Animation",
    "animation": "Animation",
    "comedy": "Comedy",
    "crime": "Crime",
    "documentary": "Documentary",
    "drama": "Drama",
    "family": "Family",
    "fantasy": "Fantasy",
    "historical": "History",
    "history": "History",
    "horror": "Horror",
    "musical": "Music",
    "music": "Music",
    "mystery": "Mystery",
    "romance": "Romance",
    "romantic": "Romance",
    "sci-fi": "Sci-Fi",
    "science": "Sci-Fi",
    "thriller": "Thriller",
    "war": "War",
    "western": "Western",
}

# Priority order when capping the genre list — we prefer broader genres over niche tags.
GENRE_PRIORITY = [
    "Drama", "Comedy", "Action", "Crime", "Thriller", "Horror", "Sci-Fi",
    "Romance", "Mystery", "Adventure", "Fantasy", "Animation", "Documentary",
    "Western", "War", "Family", "History", "Music",
]

MAX_GENRES = 4

# Map Wikidata studio/distributor labels to our studio slugs.
STUDIO_MAP = {
    "Warner Bros.": "warner-bros",
    "Warner Bros. Pictures": "warner-bros",
    "Warner Bros. Entertainment": "warner-bros",
    "New Line Cinema": "new-line",
    "Universal Pictures": "universal",
    "Universal Studios": "universal",
    "Paramount Pictures": "paramount",
    "Paramount": "paramount",
    "Walt Disney Pictures": "disney",
    "Disney": "disney",
    "20th Century Fox": "20th-century",
    "20th Century Studios": "20th-century",
    "Twentieth Century Fox": "20th-century",
    "Sony Pictures": "sony",
    "Sony Pictures Releasing": "sony",
    "Sony Pictures Entertainment": "sony",
    "Columbia Pictures": "sony",
    "TriStar Pictures": "tristar",
    "Metro-Goldwyn-Mayer": "mgm",
    "MGM": "mgm",
    "MGM/UA": "mgm",
    "United Artists": "mgm",
    "Lionsgate": "lionsgate",
    "Lionsgate Films": "lionsgate",
    "Lions Gate Films": "lionsgate",
    "A24": "a24",
    "Miramax": "miramax",
    "Miramax Films": "miramax",
    "DreamWorks": "dreamworks",
    "DreamWorks Pictures": "dreamworks",
    "DreamWorks Animation": "dreamworks",
    "Orion Pictures": "orion",
    "Fox Searchlight Pictures": "fox-searchlight",
    "Searchlight Pictures": "fox-searchlight",
    "Marvel Studios": "marvel",
    "Marvel Entertainment": "marvel",
    "Lucasfilm Ltd.": "lucasfilm",
    "Lucasfilm": "lucasfilm",
    "Apple Studios": "apple",
    "Apple TV+": "apple",
    "Gramercy Pictures": "gramercy",
    "Embassy Pictures": "embassy",
    "Working Title Films": "working-title",
    "PolyGram Filmed Entertainment": "polygram",
}


def http_get_json(url, params=None, accept="application/json"):
    query = urllib.parse.urlencode(params) if params else ""
    full = f"{url}?{query}" if query else url
    req = urllib.request.Request(full, headers={
        "User-Agent": USER_AGENT,
        "Accept": accept,
    })
    with urllib.request.urlopen(req, timeout=20) as r:
        return json.loads(r.read().decode())


def strip_episode_suffixes(title):
    """Remove episode-type suffixes like (Live), (Part Two) so we match the base movie."""
    cleaned = re.sub(r"\s*\((Live|Part\s+\w+)\)\s*$", "", title, flags=re.IGNORECASE)
    return cleaned.strip()


def find_film_qid(title):
    """Search Wikipedia for a film matching the title; return (qid, page_title) or (None, None)."""
    data = http_get_json(WIKIPEDIA_API, {
        "action": "query",
        "format": "json",
        "generator": "search",
        "gsrsearch": f"{title} film",
        "gsrlimit": 5,
        "prop": "pageprops",
        "ppprop": "wikibase_item",
    })
    pages = data.get("query", {}).get("pages", {})
    ordered = sorted(pages.values(), key=lambda p: p.get("index", 999))
    for page in ordered:
        qid = page.get("pageprops", {}).get("wikibase_item")
        if qid:
            return qid, page.get("title", "")
    return None, None


def fetch_wikidata(qid):
    """Run a SPARQL query for a film's year, directors, genres, production, and distribution."""
    query = f"""
SELECT
  (GROUP_CONCAT(DISTINCT ?pubDateStr; separator="|") AS ?pubDates)
  (GROUP_CONCAT(DISTINCT ?directorLabel; separator="|") AS ?directors)
  (GROUP_CONCAT(DISTINCT ?genreLabel; separator="|") AS ?genres)
  (GROUP_CONCAT(DISTINCT ?prodLabel; separator="|") AS ?productions)
  (GROUP_CONCAT(DISTINCT ?distLabel; separator="|") AS ?distributors)
WHERE {{
  BIND(wd:{qid} AS ?film)
  OPTIONAL {{ ?film wdt:P577 ?pubDate . BIND(STR(?pubDate) AS ?pubDateStr) }}
  OPTIONAL {{ ?film wdt:P57 ?director .
             ?director rdfs:label ?directorLabel . FILTER(LANG(?directorLabel)="en") }}
  OPTIONAL {{ ?film wdt:P136 ?genre .
             ?genre rdfs:label ?genreLabel . FILTER(LANG(?genreLabel)="en") }}
  OPTIONAL {{ ?film wdt:P272 ?prod .
             ?prod rdfs:label ?prodLabel . FILTER(LANG(?prodLabel)="en") }}
  OPTIONAL {{ ?film wdt:P750 ?dist .
             ?dist rdfs:label ?distLabel . FILTER(LANG(?distLabel)="en") }}
}}
"""
    data = http_get_json(WIKIDATA_SPARQL,
                         {"query": query, "format": "json"},
                         accept="application/sparql-results+json")
    bindings = data.get("results", {}).get("bindings", [])
    if not bindings:
        return None
    row = bindings[0]
    return {k: row.get(k, {}).get("value", "") for k in
            ["pubDates", "directors", "genres", "productions", "distributors"]}


def extract_year(pub_dates_str):
    if not pub_dates_str:
        return None
    years = []
    for d in pub_dates_str.split("|"):
        m = re.match(r"(\d{4})", d)
        if m:
            years.append(int(m.group(1)))
    return min(years) if years else None


def extract_directors(directors_str):
    if not directors_str:
        return ""
    names = [n.strip() for n in directors_str.split("|") if n.strip()]
    return ", ".join(names)


def extract_genres(genres_str):
    """Map Wikidata genre phrases to our genre set, capped to MAX_GENRES by priority."""
    if not genres_str:
        return []
    matched = set()
    for raw in genres_str.split("|"):
        phrase = raw.lower().replace(" film", "").replace("-", " ").strip()
        for token in phrase.split():
            if token in GENRE_MAP:
                matched.add(GENRE_MAP[token])
    ordered = [g for g in GENRE_PRIORITY if g in matched]
    return ordered[:MAX_GENRES]


def extract_studio(productions_str, distributors_str):
    """Prefer distributor (P750), fall back to production company (P272)."""
    for source in (distributors_str, productions_str):
        if not source:
            continue
        for label in source.split("|"):
            slug = STUDIO_MAP.get(label.strip())
            if slug:
                return slug
    return ""


def is_skeleton(episode):
    return (
        not episode.get("year")
        or not episode.get("director")
        or not episode.get("genres")
    )


def main():
    with open(EPISODES_PATH) as f:
        data = json.load(f)

    skeletons = [(i, ep) for i, ep in enumerate(data["episodes"]) if is_skeleton(ep)]

    if not skeletons:
        print("✓ No skeleton episodes to enrich")
        return 0

    print(f"Found {len(skeletons)} skeleton episode(s) to enrich\n")
    updated = 0
    not_found = 0

    for idx, episode in skeletons:
        title = episode["title"]
        search_title = strip_episode_suffixes(title)
        label = f"{title} (as \"{search_title}\")" if search_title != title else title
        print(f"  Searching: {label}")

        try:
            qid, page = find_film_qid(search_title)
            if not qid:
                print(f"  ✗ No Wikipedia film page found")
                not_found += 1
                time.sleep(0.5)
                continue

            time.sleep(0.3)  # be polite between calls
            wd = fetch_wikidata(qid)
            if not wd:
                print(f"  ✗ Wikidata returned no data for {qid}")
                not_found += 1
                time.sleep(0.5)
                continue

            year = extract_year(wd["pubDates"])
            director = extract_directors(wd["directors"])
            genres = extract_genres(wd["genres"])
            studio = extract_studio(wd["productions"], wd["distributors"])

            if year:
                data["episodes"][idx]["year"] = year
            if director:
                data["episodes"][idx]["director"] = director
            if genres:
                data["episodes"][idx]["genres"] = genres
            if studio:
                data["episodes"][idx]["studio"] = studio

            parts = []
            if year: parts.append(f"year={year}")
            if director: parts.append(f"dir={director}")
            if genres: parts.append(f"genres={','.join(genres)}")
            if studio: parts.append(f"studio={studio}")
            print(f"  ✓ {title} → {page} [{qid}] — {', '.join(parts)}")
            updated += 1

        except Exception as e:
            print(f"  ✗ Error: {e}")
            not_found += 1

        time.sleep(0.5)

    print(f"\nUpdated: {updated}")
    print(f"Not found: {not_found}")

    if updated > 0:
        with open(EPISODES_PATH, "w") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
            f.write("\n")
        print("Done!")

    if not_found > 0:
        print(f"\n⚠️  {not_found} episode(s) failed enrichment")
        return 1

    return 0


if __name__ == "__main__":
    exit(main())
