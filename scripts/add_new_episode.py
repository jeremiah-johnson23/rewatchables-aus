#!/usr/bin/env python3
"""
Automatically add new episodes from the podcast feed to the database.

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
JUSTWATCH_AU = "https://www.justwatch.com/au"

# Common hosts for validation
KNOWN_HOSTS = [
    "Bill Simmons", "Chris Ryan", "Sean Fennessey", "Van Lathan",
    "Ryen Russillo", "Kyle Brandt", "Cousin Sal", "Wesley Morris",
    "Amanda Dobbins", "Mallory Rubin", "Jason Concepcion", "Shea Serrano"
]


def fetch_feed():
    """Fetch and parse the podcast RSS feed."""
    with urllib.request.urlopen(FEED_URL, timeout=30) as response:
        xml_data = response.read()
    return ET.fromstring(xml_data)


def parse_episode_from_feed(item):
    """Parse a single episode from RSS item."""
    title = item.find('title').text or ""
    pub_date = item.find('pubDate').text or ""
    description = item.find('description').text or ""

    # Get Apple Podcasts URL if available
    apple_url = ""
    for enclosure in item.findall('.//{http://www.itunes.com/dtds/podcast-1.0.dtd}*'):
        pass  # iTunes namespace elements

    # Parse the date
    try:
        date_obj = datetime.strptime(pub_date[:16], "%a, %d %b %Y")
        date_str = date_obj.strftime("%Y-%m-%d")
    except:
        date_str = datetime.now().strftime("%Y-%m-%d")

    # Extract movie title - handle various formats
    # Format: "Movie Title" With Host Names
    # Format: 'Movie Title' With Host Names
    movie_match = re.match(r'^["\']?([^"\']+)["\']?\s+[Ww]ith', title)
    if movie_match:
        movie_title = movie_match.group(1).strip()
    else:
        movie_title = title.split(" With")[0].strip().strip('"\'')

    # Clean up movie title
    movie_title = movie_title.strip("'\"")

    # Extract hosts
    hosts = []
    hosts_match = re.search(r'[Ww]ith\s+(.+)$', title)
    if hosts_match:
        hosts_str = hosts_match.group(1)
        # Split by ", and ", " and ", or just ","
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
        'description': description
    }


def load_database():
    """Load episodes from database."""
    script_dir = Path(__file__).parent
    data_file = script_dir.parent / "src" / "data" / "episodes.json"

    with open(data_file, 'r') as f:
        data = json.load(f)
    return data, data_file


def create_episode_object(parsed_ep):
    """Create a full episode object for the database."""
    today = datetime.now().strftime("%Y-%m-%d")

    return {
        "id": parsed_ep['id'],
        "title": parsed_ep['title'],
        "year": 0,  # Will need manual update
        "director": "Unknown",  # Will need manual update
        "episodeDate": parsed_ep['date'],
        "spotifyUrl": "https://open.spotify.com/show/1lUPomulZRPquVAOOd56EW",
        "applePodcastsUrl": "",  # Can be added later
        "hosts": parsed_ep['hosts'],
        "guests": [],
        "genres": [],
        "streaming": {
            "netflix": False,
            "stan": False,
            "primeVideo": False,
            "disneyPlus": False,
            "binge": False,
            "paramount": False,
            "appleTv": False,
            "hboMax": False,
            "rentBuy": []
        },
        "lastStreamingCheck": today,
        "communityRating": {
            "average": 0,
            "votes": 0
        },
        "studio": "unknown"
    }


def find_missing_episodes(feed_items, db_episodes, limit=5):
    """Find episodes in feed that aren't in database."""
    db_dates = set(ep.get('episodeDate', '') for ep in db_episodes)
    db_titles = set(ep.get('title', '').lower() for ep in db_episodes)
    db_ids = set(ep.get('id', '') for ep in db_episodes)

    missing = []
    for item in feed_items[:limit]:
        parsed = parse_episode_from_feed(item)

        # Check if this episode exists by date, title, or ID
        if (parsed['date'] not in db_dates and
            parsed['title'].lower() not in db_titles and
            parsed['id'] not in db_ids):
            missing.append(parsed)

    return missing


def main():
    parser = argparse.ArgumentParser(description='Add new episodes to database')
    parser.add_argument('--dry-run', action='store_true', help='Show what would be added without making changes')
    parser.add_argument('--count', type=int, default=5, help='Number of recent episodes to check')

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

    print(f"Checking {args.count} recent episodes against {len(db_episodes)} in database...")

    missing = find_missing_episodes(feed_items, db_episodes, limit=args.count)

    if not missing:
        print("\n✓ Database is up to date! No new episodes found.")
        return 0

    print(f"\n{'[DRY RUN] ' if args.dry_run else ''}Found {len(missing)} new episode(s):\n")

    added = []
    for parsed_ep in missing:
        print(f"  📺 {parsed_ep['title']}")
        print(f"     Date: {parsed_ep['date']}")
        print(f"     Hosts: {', '.join(parsed_ep['hosts'])}")

        if not args.dry_run:
            new_episode = create_episode_object(parsed_ep)
            # Insert at the beginning (newest first)
            data['episodes'].insert(0, new_episode)
            added.append(parsed_ep['title'])
        print()

    if not args.dry_run and added:
        # Save the updated database
        with open(data_file, 'w') as f:
            json.dump(data, f, indent=2)

        print(f"✓ Added {len(added)} episode(s) to database")
        print("\n⚠️  Note: Year, director, genres, and streaming data need manual update")
        print(f"   Check JustWatch AU for streaming: {JUSTWATCH_AU}")

        # Output for GitHub Actions
        print(f"\n::set-output name=episodes_added::{', '.join(added)}")
        return 0

    if args.dry_run:
        print("[DRY RUN] No changes made")

    return 0


if __name__ == '__main__':
    exit(main())
