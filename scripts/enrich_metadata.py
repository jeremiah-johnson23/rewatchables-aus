#!/usr/bin/env python3
"""
Enrich skeleton episodes with metadata from TMDB.

Usage:
    python3 scripts/enrich_metadata.py

Requires TMDB_API_KEY environment variable.
Fills in: year, director, genres, studio for episodes missing that data.
"""

import json
import os
import time
import urllib.request
import urllib.parse
from pathlib import Path

EPISODES_PATH = Path(__file__).parent.parent / "src" / "data" / "episodes.json"
TMDB_BASE = "https://api.themoviedb.org/3"
TMDB_API_KEY = os.environ.get("TMDB_API_KEY", "")

# Map TMDB genre names to our genre names
GENRE_MAP = {
    "Action": "Action",
    "Adventure": "Adventure",
    "Animation": "Animation",
    "Comedy": "Comedy",
    "Crime": "Crime",
    "Documentary": "Documentary",
    "Drama": "Drama",
    "Family": "Family",
    "Fantasy": "Fantasy",
    "History": "History",
    "Horror": "Horror",
    "Music": "Music",
    "Mystery": "Mystery",
    "Romance": "Romance",
    "Science Fiction": "Sci-Fi",
    "TV Movie": "Drama",
    "Thriller": "Thriller",
    "War": "War",
    "Western": "Western",
}

# Map TMDB production company names to our studio slugs
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
    "Columbia Pictures": "sony",
    "Sony Pictures Entertainment": "sony",
    "TriStar Pictures": "tristar",
    "Metro-Goldwyn-Mayer": "mgm",
    "MGM": "mgm",
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
}


def tmdb_request(path, params=None):
    """Make a request to the TMDB API."""
    if params is None:
        params = {}
    params["api_key"] = TMDB_API_KEY
    query_string = urllib.parse.urlencode(params)
    url = f"{TMDB_BASE}{path}?{query_string}"

    req = urllib.request.Request(
        url,
        headers={"User-Agent": "Mozilla/5.0", "Accept": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=15) as response:
        return json.loads(response.read().decode())


def search_movie(title):
    """Search TMDB for a movie by title."""
    data = tmdb_request("/search/movie", {"query": title, "language": "en-US"})
    return data.get("results", [])


def get_movie_details(movie_id):
    """Get full movie details including credits."""
    details = tmdb_request(f"/movie/{movie_id}", {"language": "en-US"})
    credits = tmdb_request(f"/movie/{movie_id}/credits", {"language": "en-US"})
    details["credits"] = credits
    return details


def find_best_match(title, results):
    """Find the best matching movie from TMDB search results."""
    if not results:
        return None

    title_lower = title.lower().strip()

    # Exact title match first
    for r in results:
        if r.get("title", "").lower().strip() == title_lower:
            return r

    # Contained match
    for r in results:
        r_title = r.get("title", "").lower().strip()
        if title_lower in r_title or r_title in title_lower:
            return r

    # Fall back to first result (TMDB ranks by relevance)
    return results[0] if results else None


def extract_director(credits):
    """Extract director name(s) from credits."""
    crew = credits.get("crew", [])
    directors = [p["name"] for p in crew if p.get("job") == "Director"]
    return ", ".join(directors)


def extract_genres(details):
    """Map TMDB genres to our genre names."""
    genres = []
    for g in details.get("genres", []):
        mapped = GENRE_MAP.get(g["name"])
        if mapped and mapped not in genres:
            genres.append(mapped)
    return genres


def extract_studio(details):
    """Map the primary production company to our studio slug."""
    companies = details.get("production_companies", [])
    for company in companies:
        name = company.get("name", "")
        if name in STUDIO_MAP:
            return STUDIO_MAP[name]
    # No known mapping
    return ""


def is_skeleton(episode):
    """Check if an episode needs enrichment."""
    return (
        not episode.get("year")
        or not episode.get("director")
        or not episode.get("genres")
    )


def main():
    if not TMDB_API_KEY:
        print("Error: TMDB_API_KEY environment variable not set")
        return 1

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
        print(f"  Searching: {title}")

        try:
            results = search_movie(title)
            match = find_best_match(title, results)

            if not match:
                print(f"  ✗ No results for {title}")
                not_found += 1
                time.sleep(0.3)
                continue

            movie_id = match["id"]
            details = get_movie_details(movie_id)

            year = details.get("release_date", "")[:4]
            director = extract_director(details.get("credits", {}))
            genres = extract_genres(details)
            studio = extract_studio(details)

            if year:
                data["episodes"][idx]["year"] = int(year)
            if director:
                data["episodes"][idx]["director"] = director
            if genres:
                data["episodes"][idx]["genres"] = genres
            if studio:
                data["episodes"][idx]["studio"] = studio

            services = []
            if year:
                services.append(f"year={year}")
            if director:
                services.append(f"dir={director}")
            if genres:
                services.append(f"genres={','.join(genres)}")
            if studio:
                services.append(f"studio={studio}")

            print(f"  ✓ {title} ({year}) - {', '.join(services)}")
            updated += 1

        except Exception as e:
            print(f"  ✗ Error: {e}")
            not_found += 1

        time.sleep(0.3)

    print(f"\nUpdated: {updated}")
    print(f"Not found: {not_found}")

    if updated > 0:
        with open(EPISODES_PATH, "w") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
            f.write("\n")
        print("Done!")

    # Fail if any skeletons couldn't be enriched — makes workflow failures visible
    if not_found > 0:
        print(f"\n⚠️  {not_found} episode(s) failed TMDB enrichment")
        return 1

    return 0


if __name__ == "__main__":
    exit(main())
