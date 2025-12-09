#!/usr/bin/env python3
"""
Check for new Rewatchables episodes not yet in the database.

Usage:
    python scripts/check_new_episodes.py           # Check for new episodes
    python scripts/check_new_episodes.py --latest  # Show latest from feed
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


def parse_episodes_from_feed(root, limit=10):
    """Extract recent episodes from RSS feed."""
    episodes = []
    channel = root.find('channel')

    for item in channel.findall('item')[:limit]:
        title = item.find('title').text or ""
        pub_date = item.find('pubDate').text or ""
        description = item.find('description').text or ""

        # Parse the date
        try:
            # Format: "Tue, 03 Dec 2024 10:00:00 -0000"
            date_obj = datetime.strptime(pub_date[:16], "%a, %d %b %Y")
            date_str = date_obj.strftime("%Y-%m-%d")
        except:
            date_str = pub_date

        # Extract movie title from episode title
        # Format usually: "Movie Title" With Host Names
        movie_match = re.match(r'^["\']?([^"\']+)["\']?\s+[Ww]ith', title)
        if movie_match:
            movie_title = movie_match.group(1).strip()
        else:
            movie_title = title.split(" With")[0].strip().strip('"\'')

        # Extract hosts
        hosts_match = re.search(r'[Ww]ith\s+(.+)$', title)
        hosts = []
        if hosts_match:
            hosts_str = hosts_match.group(1)
            # Split by ", and ", " and ", or just ","
            hosts = re.split(r',\s+and\s+|,\s+|\s+and\s+', hosts_str)
            hosts = [h.strip() for h in hosts if h.strip()]

        episodes.append({
            'title': movie_title,
            'full_title': title,
            'date': date_str,
            'hosts': hosts,
            'description': description[:200] + "..." if len(description) > 200 else description
        })

    return episodes


def load_database():
    """Load episodes from database."""
    script_dir = Path(__file__).parent
    data_file = script_dir.parent / "src" / "data" / "episodes.json"

    with open(data_file, 'r') as f:
        data = json.load(f)
    return data['episodes']


def find_missing_episodes(feed_episodes, db_episodes):
    """Find episodes in feed that aren't in database."""
    # Get all episode dates from database
    db_dates = set(ep.get('episodeDate', '') for ep in db_episodes)
    db_titles = set(ep.get('title', '').lower() for ep in db_episodes)

    missing = []
    for ep in feed_episodes:
        # Check if this episode date or title exists
        if ep['date'] not in db_dates:
            # Double-check by title
            if ep['title'].lower() not in db_titles:
                missing.append(ep)

    return missing


def main():
    parser = argparse.ArgumentParser(description='Check for new Rewatchables episodes')
    parser.add_argument('--latest', action='store_true', help='Show latest episode from feed')
    parser.add_argument('--count', type=int, default=10, help='Number of feed episodes to check')

    args = parser.parse_args()

    print("Fetching podcast feed...")
    try:
        root = fetch_feed()
        feed_episodes = parse_episodes_from_feed(root, limit=args.count)
    except Exception as e:
        print(f"Error fetching feed: {e}")
        return

    if args.latest:
        ep = feed_episodes[0]
        print("\n" + "=" * 60)
        print("LATEST EPISODE")
        print("=" * 60)
        print(f"Title: {ep['full_title']}")
        print(f"Movie: {ep['title']}")
        print(f"Date: {ep['date']}")
        print(f"Hosts: {', '.join(ep['hosts'])}")
        print(f"\nDescription: {ep['description']}")
        return

    print("Loading database...")
    db_episodes = load_database()

    print(f"Checking {len(feed_episodes)} recent episodes against {len(db_episodes)} in database...")

    missing = find_missing_episodes(feed_episodes, db_episodes)

    if not missing:
        print("\n✓ Database is up to date! No new episodes found.")
    else:
        print(f"\n⚠️  Found {len(missing)} new episode(s) not in database:\n")
        for ep in missing:
            print(f"  📺 {ep['title']}")
            print(f"     Date: {ep['date']}")
            print(f"     Hosts: {', '.join(ep['hosts'])}")
            print()

        print("To add these, run a session and say 'add new episodes'")


if __name__ == '__main__':
    main()
