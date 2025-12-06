#!/usr/bin/env python3
"""
Fetch New Episodes Script
Checks the Rewatchables RSS feed for episodes not in the database.

Usage:
    python3 scripts/fetch_new_episodes.py

Output:
    Prints any new episodes found as JSON objects ready to add to episodes.json
"""

import json
import re
import xml.etree.ElementTree as ET
from datetime import datetime
from pathlib import Path
from urllib.request import urlopen

RSS_URL = "https://feeds.megaphone.fm/the-rewatchables"
EPISODES_PATH = Path(__file__).parent.parent / "src" / "data" / "episodes.json"

# Known hosts for attribution
KNOWN_HOSTS = [
    "Bill Simmons", "Chris Ryan", "Sean Fennessey", "Van Lathan",
    "Mallory Rubin", "Amanda Dobbins", "Wesley Morris", "Ryen Russillo",
    "Shea Serrano", "Jason Concepcion", "Andy Greenwald", "Juliet Litman",
    "Craig Horlbeck", "Danny Heifetz", "Danny Kelly"
]

# Skip non-movie episodes
SKIP_PATTERNS = [
    r"category selection",
    r"selection show",
    r"new categories",
    r"announcement",
    r"preview",
    r"mailbag",
    r"live from",
    r"bonus:",
    r"^intro:",
    r"^welcome to",
    r"the re-",  # Re-episodes are rewatches of existing entries
    r"the three-",  # Special episodes
    r"\d+th anniversary",  # Anniversary rewatches
    r"live$",  # Live episodes
]


def fetch_rss():
    """Fetch and parse RSS feed."""
    with urlopen(RSS_URL, timeout=30) as response:
        return ET.parse(response)


def normalize_title(title):
    """Normalize title for comparison (lowercase, standardize quotes)."""
    title = title.lower()
    # Replace curly quotes with straight
    title = title.replace("\u2019", "'").replace("\u2018", "'")
    title = title.replace("\u201c", '"').replace("\u201d", '"')
    return title


def load_existing_episodes():
    """Load existing episodes from JSON."""
    with open(EPISODES_PATH) as f:
        data = json.load(f)
    return {normalize_title(ep["title"]): ep for ep in data["episodes"]}


def parse_title(raw_title):
    """Extract movie title from episode title."""
    # Remove "The Rewatchables: " prefix
    title = re.sub(r"^The Rewatchables:\s*", "", raw_title, flags=re.IGNORECASE)
    # Remove "With Bill Simmons..." and everything after
    title = re.sub(r"\s+[Ww]ith\s+.*$", "", title)
    # Remove "'The Re-...' suffix patterns
    title = re.sub(r"\s*['\"]\s*The Re-.*$", "", title)
    # Remove (Part One), (Part Two) etc
    title = re.sub(r"\s*\(Part\s+\w+\)", "", title, flags=re.IGNORECASE)
    # Remove year in parentheses like (1987)
    title = re.sub(r"\s*\(\d{4}\)", "", title)
    # Strip all types of quotes (straight and curly)
    title = title.strip()
    title = re.sub(r"^[\u2018\u2019\u201C\u201D'\"\u2032\u2033]+", "", title)
    title = re.sub(r"[\u2018\u2019\u201C\u201D'\"\u2032\u2033]+$", "", title)
    return title.strip()


def extract_hosts(description):
    """Try to extract hosts from episode description."""
    hosts = []
    for host in KNOWN_HOSTS:
        if host.lower() in description.lower():
            hosts.append(host)
    return hosts if hosts else ["Bill Simmons"]


def should_skip(title):
    """Check if episode should be skipped (non-movie content)."""
    title_lower = title.lower()
    return any(re.search(pattern, title_lower) for pattern in SKIP_PATTERNS)


def create_episode_id(title):
    """Generate episode ID from title."""
    # Remove special characters, convert to kebab-case
    slug = re.sub(r"[^\w\s-]", "", title.lower())
    slug = re.sub(r"[\s_]+", "-", slug)
    return slug.strip("-")


def main():
    print("Fetching RSS feed...")
    tree = fetch_rss()
    root = tree.getroot()
    channel = root.find("channel")

    print("Loading existing episodes...")
    existing = load_existing_episodes()

    new_episodes = []

    for item in channel.findall("item"):
        raw_title = item.find("title").text or ""
        title = parse_title(raw_title)

        if should_skip(title):
            continue

        # Check if already exists
        if normalize_title(title) in existing:
            continue

        # Parse date
        pub_date = item.find("pubDate").text
        try:
            dt = datetime.strptime(pub_date, "%a, %d %b %Y %H:%M:%S %z")
            episode_date = dt.strftime("%Y-%m-%d")
        except:
            episode_date = datetime.now().strftime("%Y-%m-%d")

        # Get description for host extraction
        description = item.find("description").text or ""
        hosts = extract_hosts(description)

        # Build episode object
        episode = {
            "id": create_episode_id(title),
            "title": title,
            "year": None,  # Fill in manually
            "director": "",  # Fill in manually
            "episodeDate": episode_date,
            "spotifyUrl": "https://open.spotify.com/show/1lUPomulZRPquVAOOd56EW",
            "applePodcastsUrl": "https://podcasts.apple.com/au/podcast/the-rewatchables/id1320353041",
            "hosts": hosts,
            "guests": [],
            "genres": [],  # Fill in manually
            "streaming": {
                "netflix": False,
                "stan": False,
                "primeVideo": False,
                "disneyPlus": False,
                "binge": False,
                "paramount": False,
                "appleTv": False,
                "rentBuy": []
            },
            "lastStreamingCheck": datetime.now().strftime("%Y-%m-%d"),
            "communityRating": {
                "average": 0,
                "votes": 0
            }
        }

        new_episodes.append(episode)

    if not new_episodes:
        print("\nNo new episodes found!")
        return

    print(f"\nFound {len(new_episodes)} new episode(s):\n")

    for ep in new_episodes:
        print(f"--- {ep['title']} ({ep['episodeDate']}) ---")
        print(json.dumps(ep, indent=2))
        print()

    print("\nTo add these episodes:")
    print("1. Copy the JSON above")
    print("2. Add to src/data/episodes.json in the 'episodes' array")
    print("3. Fill in: year, director, genres")
    print("4. Check streaming on https://www.justwatch.com/au")
    print("5. Commit and push")


if __name__ == "__main__":
    main()
