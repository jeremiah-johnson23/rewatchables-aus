#!/usr/bin/env python3
"""
Fetch Apple Podcasts URLs for each episode.

Usage:
    python3 scripts/fetch_apple_podcast_urls.py

This script searches Apple Podcasts for each episode and updates episodes.json
with direct episode links.
"""

import json
import re
import time
import urllib.request
import urllib.parse
from pathlib import Path

EPISODES_PATH = Path(__file__).parent.parent / "src" / "data" / "episodes.json"
APPLE_SEARCH_URL = "https://itunes.apple.com/search"

def search_apple_podcasts(title, retries=3):
    """Search Apple Podcasts for an episode."""
    query = urllib.parse.quote(f"The Rewatchables {title}")
    url = f"{APPLE_SEARCH_URL}?term={query}&entity=podcastEpisode&limit=5"

    for attempt in range(retries):
        try:
            req = urllib.request.Request(url)
            req.add_header('User-Agent', 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)')
            with urllib.request.urlopen(req, timeout=15) as response:
                data = json.loads(response.read().decode())
                return data.get('results', [])
        except Exception as e:
            if attempt < retries - 1:
                wait_time = (attempt + 1) * 2
                time.sleep(wait_time)
            else:
                print(f"  Error: {e}")
                return []
    return []


def _normalize_for_match(s):
    """Lowercase and drop all quote characters. Apple wraps film names in
    single quotes ('Good Will Hunting' Live From Boston) so the closing
    quote ends up *inside* film_part after the " with <hosts>" split,
    breaking prefix matching. Stripping all quotes side-steps the issue and
    also folds typographic apostrophes vs straight on both needle and
    track name (e.g. 'Devil's Advocate' → 'devils advocate' on both sides)."""
    s = s.lower()
    s = re.sub(r"[‘’“”'\"]", "", s)
    return s


def find_best_match(title, results, year=None):
    """Find the best matching episode from search results.

    Ranks candidates so an exact title match wins over a sibling-film substring.
    Substring containment alone is too loose: searching "Rocky" used to match
    "Rocky II With Bill Simmons…" because the substring is present.

    Returns the URL of the best candidate, or None if nothing scores confidently.
    """
    # Stored titles use "(Live)" / "(Live Show)" to flag entries that
    # represent a live-show episode. Strip the marker from the needle (Apple
    # titles live shows freely as "Live From SF" etc.) but keep a flag so we
    # can prefer the live-variant track for these entries — and conversely
    # prefer the non-live track for entries without the marker.
    is_live_entry = bool(re.search(r'\(live(?:\s+show)?\)\s*$', title, re.IGNORECASE))
    needle = re.sub(r'\s*\(live(?:\s+show)?\)\s*$', '', title, flags=re.IGNORECASE)
    needle = _normalize_for_match(needle).strip()

    candidates = []
    for result in results:
        if 'rewatchables' not in result.get('collectionName', '').lower():
            continue
        track_raw = result.get('trackName', '')
        # Apple's host preamble: " With " followed by a capital-letter first
        # name (Bill, Chris, Sean…). Film-title "With" connectors are followed
        # by lowercase articles ("Die Hard With a Vengeance", "Gone With the
        # Wind"). Require a capital letter after "With" so we split at the
        # host preamble, not inside a film title. Also handle "Featuring"
        # which Apple uses occasionally.
        film_raw = re.split(r'\s+(?:With|Featuring)\s+(?=[A-Z])', track_raw, maxsplit=1)[0]
        track_name = _normalize_for_match(track_raw)
        film_part = _normalize_for_match(film_raw).strip()
        # Apple wraps film titles in quotes ('Rocky', ‘Top Gun’) — strip the
        # wrapping pair so exact-match comparison works. Preserves internal
        # apostrophes like in "Mr. Holland's Opus". Also drop a trailing period
        # that Apple sometimes leaves outside the closing quote ("'48 Hrs'.").
        film_part = film_part.strip("'\"")
        film_part = re.sub(r"[\s'\".]+$", "", film_part).strip()
        film_clean = re.sub(r'\s+\(?\d{4}\)?\s*$', '', film_part).strip()

        if film_clean == needle:
            # Exact non-live match. Prefer when entry is non-live; demote when
            # entry is the live-show variant.
            score = 30 if is_live_entry else 100
        elif film_part == needle:
            score = 30 if is_live_entry else 95
        elif film_clean.startswith(needle + ' ') or film_clean.startswith(needle + '-'):
            # Distinguish multi-part episodes (Pulp Fiction Part 1) and
            # live-show variants (Good Will Hunting Live From Boston) from
            # sibling films (Rocky II, Top Gun Maverick).
            extension = film_clean[len(needle):].lstrip(' -')
            if re.match(r'(part|pt)\s+(\d+|i+)\b', extension):
                score = 90   # multi-part episode of the named film
            elif re.match(r'live(\s+from\b|$)', extension):
                # Live variant of the named film. Prefer when entry is live;
                # demote when entry is non-live (so original wins).
                score = 100 if is_live_entry else 30
            elif re.match(r'\d+(st|nd|rd|th)\s+anniversary\b', extension):
                # Anniversary re-cover of the named film (e.g. "Die Hard 30th
                # Anniversary"). Treat as the canonical episode for the named
                # film when no non-suffixed exact match exists.
                score = 90 if not is_live_entry else 30
            else:
                score = 25   # likely sibling
        elif needle in track_name:
            # Substring match. Bump if the entry is (Live Show) and the track
            # carries a live marker ("LIVE" / "Live From X" anywhere in the
            # film_part, before the " with <hosts>" preamble). Apple titles
            # live re-cover episodes like "The Re-'Den of Thieves' LIVE With
            # Bill Simmons" — film_part is "the re-den of thieves live".
            if is_live_entry and re.search(r'\blive\b', film_part):
                score = 80
            else:
                score = 15   # bare substring, low confidence
        else:
            continue

        # Year handling. Apple often disambiguates same-name films with a year
        # suffix ("Bad Boys 1983"). Boost when stored year corroborates the
        # track; demote when a different year appears in the film_part, which
        # almost always means we matched the wrong same-name film.
        if year:
            if re.search(rf'\b{year}\b', track_name):
                score += 50
            else:
                film_year = re.search(r'\b(\d{4})\b', film_part)
                if film_year and film_year.group(1) != str(year):
                    score -= 70

        candidates.append((score, result.get('trackViewUrl')))

    if not candidates:
        return None
    candidates.sort(key=lambda x: -x[0])
    best_score, best_url = candidates[0]
    # Reject low-confidence matches. A prefix-only hit without a year corroboration
    # is almost always the wrong sibling — better to leave the URL alone than
    # confidently link to a different film's episode.
    if best_score < 50:
        return None
    return best_url


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Fetch Apple Podcasts URLs for episodes")
    parser.add_argument("--force", action="store_true",
                        help="Re-fetch even for entries that already have an episode URL")
    parser.add_argument("--ids", help="Comma-separated episode ids to limit the run to")
    args = parser.parse_args()

    target_ids = set(s.strip() for s in args.ids.split(",")) if args.ids else None

    print("Loading episodes...")
    with open(EPISODES_PATH) as f:
        data = json.load(f)

    episodes = data['episodes']
    updated = 0
    unchanged = 0
    skipped = 0
    not_found = 0

    print(f"Processing {len(episodes)} episodes...\n")

    for i, episode in enumerate(episodes):
        title = episode['title']
        year = episode.get('year')
        current_url = episode.get('applePodcastsUrl', '')

        if target_ids and episode.get('id') not in target_ids:
            continue

        # Skip if already has an episode-specific URL (unless --force)
        if '?i=' in current_url and not args.force:
            skipped += 1
            continue

        print(f"[{i+1}/{len(episodes)}] {title} ({year})...")

        results = search_apple_podcasts(title)
        url = find_best_match(title, results, year=year) if results else None

        # Year-augmented retry if first pass was rejected as low-confidence
        if not url and year:
            results = search_apple_podcasts(f"{title} {year}")
            url = find_best_match(title, results, year=year) if results else None

        if url:
            url = url.replace('/us/', '/au/')
            if url == current_url:
                print(f"  = Unchanged")
                unchanged += 1
            else:
                episode['applePodcastsUrl'] = url
                old_short = (current_url.split('?i=')[-1] or '<none>')[:18]
                new_short = url.split('?i=')[-1][:18]
                print(f"  ✓ {('updated' if current_url else 'set')}: i={old_short} → i={new_short}")
                updated += 1
        else:
            print(f"  ✗ No confident match (existing URL left untouched)")
            not_found += 1

        # Rate limit - be nice to the API
        time.sleep(1.5)

    print(f"\n--- Summary ---")
    print(f"Updated: {updated}")
    print(f"Unchanged (already correct): {unchanged}")
    print(f"Skipped (already have URL): {skipped}")
    print(f"Not found: {not_found}")

    if updated > 0:
        print(f"\nSaving to {EPISODES_PATH}...")
        with open(EPISODES_PATH, 'w') as f:
            json.dump(data, f, indent=2)
        print("Done!")
    else:
        print("\nNo updates to save.")


if __name__ == "__main__":
    main()
