#!/usr/bin/env python3
"""
Automatically add new episodes from the podcast feed to the database.
Adds episodes with basic info from RSS - metadata filled manually or via lookup.

Usage:
    python scripts/add_new_episode.py           # Add any missing episodes
    python scripts/add_new_episode.py --dry-run # Show what would be added
"""

import json
import re
import argparse
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime
from pathlib import Path

FEED_URL = "https://feeds.megaphone.fm/the-rewatchables"


def fetch_feed():
    """Fetch and parse the podcast RSS feed."""
    with urllib.request.urlopen(FEED_URL, timeout=30) as response:
        xml_data = response.read()
    return ET.fromstring(xml_data)


def get_default_streaming():
    """Return default streaming object (all false, to be filled manually)."""
    return {
        "netflix": False,
        "stan": False,
        "primeVideo": False,
        "disneyPlus": False,
        "binge": False,
        "paramount": False,
        "appleTv": False,
        "hboMax": False,
        "rentBuy": []
    }


def parse_episode_from_feed(item):
    """Parse a single episode from RSS item."""
    title = item.find('title').text or ""
    pub_date = item.find('pubDate').text or ""

    # Parse the date
    try:
        date_obj = datetime.strptime(pub_date[:16], "%a, %d %b %Y")
        date_str = date_obj.strftime("%Y-%m-%d")
    except:
        date_str = datetime.now().strftime("%Y-%m-%d")

    # Extract movie title
    movie_match = re.match(r'^["\']?([^"\']+)["\']?\s+[Ww]ith', title)
    if movie_match:
        movie_title = movie_match.group(1).strip()
    else:
        movie_title = title.split(" With")[0].strip().strip('"\'')

    movie_title = movie_title.strip("'\"")

    # Extract hosts
    hosts = []
    hosts_match = re.search(r'[Ww]ith\s+(.+)$', title)
    if hosts_match:
        hosts_str = hosts_match.group(1)
        raw_hosts = re.split(r',\s+and\s+|,\s+|\s+and\s+', hosts_str)
        hosts = [h.strip() for h in raw_hosts if h.strip()]

    # Generate episode ID
    episode_id = re.sub(r'[^a-z0-9]+', '-', movie_title.lower()).strip('-')

    return {
        'id': episode_id,
        'title': movie_title,
        'full_title': title,
        'date': date_str,
        'hosts': hosts,
    }


def load_database():
    """Load episodes from database."""
    script_dir = Path(__file__).parent
    data_file = script_dir.parent / "src" / "data" / "episodes.json"

    with open(data_file, 'r') as f:
        data = json.load(f)
    return data, data_file


def create_episode_object(parsed_ep):
    """Create episode object with RSS data. Metadata to be filled manually."""
    today = datetime.now().strftime("%Y-%m-%d")

    # Clean up title (remove curly quotes)
    title = parsed_ep['title'].replace('\u2018', "'").replace('\u2019', "'")
    title = title.replace('\u201c', '"').replace('\u201d', '"')
    title = title.strip("'\"")

    print(f"  Adding: {title} ({parsed_ep['date']})")
    print(f"    Hosts: {', '.join(parsed_ep['hosts']) if parsed_ep['hosts'] else 'Unknown'}")
    print(f"    ⚠️  Needs: year, director, genres, studio, streaming (check JustWatch AU)")

    return {
        "id": parsed_ep['id'],
        "title": title,
        "year": None,
        "director": "",
        "episodeDate": parsed_ep['date'],
        "spotifyUrl": "https://open.spotify.com/show/1lUPomulZRPquVAOOd56EW",
        "applePodcastsUrl": "https://podcasts.apple.com/au/podcast/the-rewatchables/id1320353041",
        "hosts": parsed_ep['hosts'],
        "guests": [],
        "genres": [],
        "streaming": get_default_streaming(),
        "lastStreamingCheck": today,
        "communityRating": {
            "average": 0,
            "votes": 0
        },
        "studio": ""
    }


def find_missing_episodes(feed_items, db_episodes, limit=5):
    """Find episodes in feed that aren't in database."""
    db_dates = set(ep.get('episodeDate', '') for ep in db_episodes)
    db_titles = set(ep.get('title', '').lower() for ep in db_episodes)

    missing = []
    for item in feed_items[:limit]:
        parsed = parse_episode_from_feed(item)

        if (parsed['date'] not in db_dates and
            parsed['title'].lower() not in db_titles):
            missing.append(parsed)

    return missing


def main():
    parser = argparse.ArgumentParser(description='Add new episodes to database')
    parser.add_argument('--dry-run', action='store_true', help='Show what would be added')
    parser.add_argument('--count', type=int, default=5, help='Episodes to check')

    args = parser.parse_args()

    print("Fetching podcast feed...")
    try:
        root = fetch_feed()
        channel = root.find('channel')
        feed_items = channel.findall('item')
    except Exception as e:
        print(f"Error fetching feed: {e}")
        return 1

    print("Loading database...")
    data, data_file = load_database()
    db_episodes = data['episodes']

    print(f"Checking {args.count} recent episodes...\n")

    missing = find_missing_episodes(feed_items, db_episodes, limit=args.count)

    if not missing:
        print("✓ Database is up to date!")
        return 0

    print(f"Found {len(missing)} new episode(s):\n")

    added = []
    for parsed_ep in missing:
        print(f"📺 Adding: {parsed_ep['title']} ({parsed_ep['date']})")

        if not args.dry_run:
            new_episode = create_episode_object(parsed_ep)
            data['episodes'].insert(0, new_episode)
            added.append(new_episode['title'])
        print()

    if not args.dry_run and added:
        with open(data_file, 'w') as f:
            json.dump(data, f, indent=2)

        print(f"\n✓ Added {len(added)} episode(s) to database")
        print("\nTo complete these entries:")
        print("1. Look up each movie on JustWatch AU for streaming")
        print("2. Add year, director, genres, studio to episodes.json")
        return 0

    if args.dry_run:
        print("[DRY RUN] No changes made")

    return 0


if __name__ == '__main__':
    exit(main())
