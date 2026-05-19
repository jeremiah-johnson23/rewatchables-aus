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
    """Lowercase and fold curly quotes to straight so substring checks survive
    Apple's typographic quoting (`'There's...'` with U+2018/U+2019)."""
    s = s.lower()
    s = s.replace('‘', "'").replace('’', "'")
    s = s.replace('“', '"').replace('”', '"')
    return s


def find_best_match(title, results, year=None):
    """Find the best matching episode from search results.

    Ranks candidates so an exact title match wins over a sibling-film substring.
    Substring containment alone is too loose: searching "Rocky" used to match
    "Rocky II With Bill Simmons…" because the substring is present.

    Returns the URL of the best candidate, or None if nothing scores confidently.
    """
    # Drop our internal "(Live)" / "(Live Show)" markers — Apple titles phrase
    # live shows freely ("Live From SF"), so requiring them in the track name
    # would miss legitimate matches.
    needle = re.sub(r'\s*\(live(?:\s+show)?\)\s*$', '', title, flags=re.IGNORECASE)
    needle = _normalize_for_match(needle).strip()

    candidates = []
    for result in results:
        if 'rewatchables' not in result.get('collectionName', '').lower():
            continue
        track_name = _normalize_for_match(result.get('trackName', ''))
        # Strip " with <hosts>" preamble and any trailing "(YYYY)"/"YYYY"
        film_part = re.split(r'\s+with\s+', track_name, maxsplit=1)[0].strip()
        film_clean = re.sub(r'\s+\(?\d{4}\)?\s*$', '', film_part).strip()

        if film_clean == needle:
            score = 100  # exact film match (year stripped)
        elif film_part == needle:
            score = 95   # exact including year
        elif film_clean.startswith(needle + ' ') or film_clean.startswith(needle + '-'):
            # Distinguish multi-part episodes (Pulp Fiction Part 1) from
            # sibling films (Rocky II, Top Gun Maverick).
            extension = film_clean[len(needle):].lstrip(' -')
            if re.match(r'(part|pt)\s+(\d+|i+)\b', extension):
                score = 90   # multi-part episode of the named film
            elif re.match(r'live(\s+from\b|$)', extension):
                score = 90   # live-show variant of the named film
            else:
                score = 25   # likely sibling
        elif needle in track_name:
            score = 15   # substring anywhere
        else:
            continue

        # Year corroboration: Apple often includes year in older-film titles
        # ("Rocky 1976 With Bill Simmons…"). Use as a strong tiebreaker.
        if year and re.search(rf'\b{year}\b', track_name):
            score += 50

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
