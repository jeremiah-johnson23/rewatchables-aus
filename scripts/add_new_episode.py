#!/usr/bin/env python3
"""
Automatically add new episodes from the podcast feed to the database.
Fetches all metadata: year, director, genres, streaming, studio.

Usage:
    python scripts/add_new_episode.py           # Add any missing episodes
    python scripts/add_new_episode.py --dry-run # Show what would be added
"""

import json
import re
import argparse
import urllib.request
import urllib.parse
import xml.etree.ElementTree as ET
from datetime import datetime
from pathlib import Path

FEED_URL = "https://feeds.megaphone.fm/the-rewatchables"
OMDB_API_KEY = "db0fdf04"  # Free tier key

# Studio mappings based on distributor
DISTRIBUTOR_TO_STUDIO = {
    "warner": "warner-bros",
    "warner bros": "warner-bros",
    "new line": "new-line",
    "disney": "disney",
    "walt disney": "disney",
    "pixar": "pixar",
    "marvel": "marvel",
    "lucasfilm": "lucasfilm",
    "20th century": "20th-century",
    "twentieth century": "20th-century",
    "fox searchlight": "fox-searchlight",
    "searchlight": "fox-searchlight",
    "paramount": "paramount",
    "miramax": "miramax",
    "mgm": "mgm",
    "metro-goldwyn": "mgm",
    "united artists": "mgm",
    "amazon": "amazon",
    "universal": "universal",
    "sony": "sony",
    "columbia": "sony",
    "tristar": "tristar",
    "tri-star": "tristar",
    "lionsgate": "lionsgate",
    "lions gate": "lionsgate",
    "a24": "a24",
    "orion": "orion",
    "dreamworks": "dreamworks",
}

# Studio to native streamer
NATIVE_STREAMING = {
    "warner-bros": "hboMax",
    "new-line": "hboMax",
    "disney": "disneyPlus",
    "pixar": "disneyPlus",
    "marvel": "disneyPlus",
    "lucasfilm": "disneyPlus",
    "20th-century": "disneyPlus",
    "fox-searchlight": "disneyPlus",
    "paramount": "paramount",
    "miramax": "paramount",
    "mgm": "primeVideo",
    "amazon": "primeVideo",
}


def fetch_feed():
    """Fetch and parse the podcast RSS feed."""
    with urllib.request.urlopen(FEED_URL, timeout=30) as response:
        xml_data = response.read()
    return ET.fromstring(xml_data)


def fetch_movie_data(title, year=None):
    """Fetch movie data from OMDB API."""
    params = {"t": title, "apikey": OMDB_API_KEY}
    if year:
        params["y"] = year

    url = f"http://www.omdbapi.com/?{urllib.parse.urlencode(params)}"

    try:
        with urllib.request.urlopen(url, timeout=10) as response:
            data = json.loads(response.read())
            if data.get("Response") == "True":
                return data
    except Exception as e:
        print(f"    Warning: Could not fetch OMDB data: {e}")

    return None


def fetch_justwatch_streaming(title):
    """
    Attempt to get streaming data from JustWatch.
    Returns dict of service availability.
    """
    # JustWatch doesn't have a public API, so we'll rely on OMDB + studio logic
    # For now, return empty and let native streaming logic fill in what we can
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


def determine_studio(production_companies, distributor):
    """Determine studio from production/distribution info."""
    # Combine and lowercase for matching
    combined = f"{production_companies} {distributor}".lower()

    for keyword, studio in DISTRIBUTOR_TO_STUDIO.items():
        if keyword in combined:
            return studio

    return "unknown"


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
    """Create a full episode object with all metadata."""
    today = datetime.now().strftime("%Y-%m-%d")

    print(f"  Fetching metadata for: {parsed_ep['title']}")

    # Fetch movie data from OMDB
    movie_data = fetch_movie_data(parsed_ep['title'])

    year = 0
    director = "Unknown"
    genres = []
    studio = "unknown"

    if movie_data:
        # Year
        try:
            year = int(movie_data.get("Year", "0")[:4])
        except:
            year = 0

        # Director
        director = movie_data.get("Director", "Unknown")
        if director == "N/A":
            director = "Unknown"

        # Genres
        genre_str = movie_data.get("Genre", "")
        if genre_str and genre_str != "N/A":
            genres = [g.strip() for g in genre_str.split(",")]

        # Studio from production company
        production = movie_data.get("Production", "")
        # OMDB doesn't always have production, try to infer from other fields
        studio = determine_studio(
            production,
            movie_data.get("DVD", "") + " " + movie_data.get("BoxOffice", "")
        )

        print(f"    Found: {parsed_ep['title']} ({year}) dir. {director}")
        print(f"    Genres: {', '.join(genres) if genres else 'None found'}")
        print(f"    Studio: {studio}")
    else:
        print(f"    Warning: No OMDB data found for {parsed_ep['title']}")

    # Build streaming object
    streaming = fetch_justwatch_streaming(parsed_ep['title'])

    # If we know the studio, set native streaming as likely available
    if studio in NATIVE_STREAMING:
        native_service = NATIVE_STREAMING[studio]
        streaming[native_service] = True
        print(f"    Native streaming: {native_service} (based on studio)")

    # Update episode ID to include year if we have it
    episode_id = parsed_ep['id']
    if year > 0:
        # Check if year already in ID
        if not re.search(r'\d{4}$', episode_id):
            episode_id = f"{episode_id}-{year}"

    return {
        "id": episode_id,
        "title": parsed_ep['title'],
        "year": year,
        "director": director,
        "episodeDate": parsed_ep['date'],
        "spotifyUrl": "https://open.spotify.com/show/1lUPomulZRPquVAOOd56EW",
        "applePodcastsUrl": "",
        "hosts": parsed_ep['hosts'],
        "guests": [],
        "genres": genres,
        "streaming": streaming,
        "lastStreamingCheck": today,
        "communityRating": {
            "average": 0,
            "votes": 0
        },
        "studio": studio
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

        print(f"✓ Added {len(added)} episode(s) to database")
        print("\nNote: Streaming data is estimated from studio ownership.")
        print("Manual verification on JustWatch AU recommended.")
        return 0

    if args.dry_run:
        print("[DRY RUN] No changes made")

    return 0


if __name__ == '__main__':
    exit(main())
