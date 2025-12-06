#!/usr/bin/env python3
"""
Fetch Apple Podcasts URLs for each episode.

Usage:
    python3 scripts/fetch_apple_podcast_urls.py

This script searches Apple Podcasts for each episode and updates episodes.json
with direct episode links.
"""

import json
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


def find_best_match(title, results):
    """Find the best matching episode from search results."""
    title_lower = title.lower()

    for result in results:
        track_name = result.get('trackName', '').lower()
        # Check if our title appears in the track name
        if title_lower in track_name:
            # Make sure it's from The Rewatchables
            collection = result.get('collectionName', '').lower()
            if 'rewatchables' in collection:
                return result.get('trackViewUrl')

    return None


def main():
    print("Loading episodes...")
    with open(EPISODES_PATH) as f:
        data = json.load(f)

    episodes = data['episodes']
    updated = 0
    skipped = 0
    not_found = 0

    print(f"Processing {len(episodes)} episodes...\n")

    for i, episode in enumerate(episodes):
        title = episode['title']
        current_url = episode.get('applePodcastsUrl', '')

        # Skip if already has an episode-specific URL (contains ?i=)
        if '?i=' in current_url:
            skipped += 1
            continue

        print(f"[{i+1}/{len(episodes)}] {title}...")

        results = search_apple_podcasts(title)

        if results:
            url = find_best_match(title, results)
            if url:
                # Convert to AU store
                url = url.replace('/us/', '/au/')
                episode['applePodcastsUrl'] = url
                print(f"  ✓ Found: {url[:60]}...")
                updated += 1
            else:
                print(f"  ✗ No match in results")
                not_found += 1
        else:
            print(f"  ✗ No results")
            not_found += 1

        # Rate limit - be nice to the API
        time.sleep(1.5)

    print(f"\n--- Summary ---")
    print(f"Updated: {updated}")
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
