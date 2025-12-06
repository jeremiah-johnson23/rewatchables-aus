#!/usr/bin/env python3
"""
Fetch streaming availability from JustWatch for Australian services.

Usage:
    python3 scripts/fetch_streaming_availability.py

This script searches JustWatch for each movie and updates episodes.json
with Australian streaming availability.
"""

import json
import time
import urllib.request
from pathlib import Path

EPISODES_PATH = Path(__file__).parent.parent / "src" / "data" / "episodes.json"
JUSTWATCH_GRAPHQL = "https://apis.justwatch.com/graphql"

# Map JustWatch package IDs to our keys
PROVIDER_MAP = {
    8: "netflix",
    21: "stan",
    119: "primeVideo",
    9: "primeVideo",  # Amazon Prime Video
    337: "disneyPlus",
    385: "binge",
    531: "paramount",
    350: "appleTv",
    1796: "netflix",  # Netflix with Ads
    1899: "stan",     # Stan alternate
}

RENT_BUY_PROVIDERS = {
    2: "Apple TV",
    3: "Google Play",
    10: "Amazon",
    192: "YouTube",
    68: "Microsoft Store",
}

GRAPHQL_QUERY = """
query GetSearchTitles($country: Country!, $searchTitlesFilter: TitleFilter!, $first: Int!) {
  popularTitles(country: $country, filter: $searchTitlesFilter, first: $first) {
    edges {
      node {
        id
        objectId
        objectType
        content(country: $country, language: "en") {
          title
          originalReleaseYear
        }
        offers(country: $country, platform: WEB) {
          monetizationType
          package {
            packageId
            clearName
          }
        }
      }
    }
  }
}
"""


def search_justwatch(title, year=None):
    """Search JustWatch for a movie and get streaming offers."""
    search_query = f"{title} {year}" if year else title

    variables = {
        "country": "AU",
        "searchTitlesFilter": {
            "searchQuery": search_query
        },
        "first": 5
    }

    payload = json.dumps({
        "query": GRAPHQL_QUERY,
        "variables": variables
    }).encode("utf-8")

    try:
        req = urllib.request.Request(
            JUSTWATCH_GRAPHQL,
            data=payload,
            headers={
                "Content-Type": "application/json",
                "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)"
            }
        )
        with urllib.request.urlopen(req, timeout=15) as response:
            data = json.loads(response.read().decode())
            return data.get("data", {}).get("popularTitles", {}).get("edges", [])
    except Exception as e:
        print(f"  Error: {e}")
        return []


def find_best_match(title, year, results):
    """Find the best matching movie from search results."""
    if not results:
        return None

    title_lower = title.lower()

    for edge in results:
        node = edge.get("node", {})
        if node.get("objectType") != "MOVIE":
            continue

        content = node.get("content", {})
        item_title = content.get("title", "").lower()
        item_year = content.get("originalReleaseYear")

        # Exact or close title match with year
        if title_lower in item_title or item_title in title_lower:
            if year and item_year:
                if abs(item_year - year) <= 1:
                    return node
            elif not year:
                return node

    # Fallback to first movie result
    for edge in results:
        node = edge.get("node", {})
        if node.get("objectType") == "MOVIE":
            content = node.get("content", {})
            item_year = content.get("originalReleaseYear")
            if year and item_year and abs(item_year - year) <= 1:
                return node

    return None


def parse_offers(node):
    """Parse streaming offers from movie node."""
    streaming = {
        "netflix": False,
        "stan": False,
        "primeVideo": False,
        "disneyPlus": False,
        "binge": False,
        "paramount": False,
        "appleTv": False,
        "rentBuy": []
    }

    offers = node.get("offers", [])
    if not offers:
        return streaming

    rent_buy_names = set()

    for offer in offers:
        package = offer.get("package", {})
        package_id = package.get("packageId")
        monetization = offer.get("monetizationType")

        if monetization == "FLATRATE":
            # Subscription streaming
            if package_id in PROVIDER_MAP:
                streaming[PROVIDER_MAP[package_id]] = True
        elif monetization in ("RENT", "BUY"):
            # Rent/Buy
            if package_id in RENT_BUY_PROVIDERS:
                rent_buy_names.add(RENT_BUY_PROVIDERS[package_id])

    streaming["rentBuy"] = sorted(list(rent_buy_names))
    return streaming


def main():
    print("Loading episodes...")
    with open(EPISODES_PATH) as f:
        data = json.load(f)

    episodes = data["episodes"]
    updated = 0
    not_found = 0
    already_has = 0

    print(f"Processing {len(episodes)} episodes...\n")

    for i, episode in enumerate(episodes):
        title = episode["title"]
        year = episode.get("year")
        current_streaming = episode.get("streaming", {})

        # Skip if already has streaming data
        has_streaming = any(
            current_streaming.get(k) for k in
            ["netflix", "stan", "primeVideo", "disneyPlus", "binge", "paramount", "appleTv"]
        ) or current_streaming.get("rentBuy")

        if has_streaming:
            already_has += 1
            continue

        print(f"[{i+1}/{len(episodes)}] {title} ({year or 'no year'})...")

        results = search_justwatch(title, year)
        node = find_best_match(title, year, results)

        if node:
            content = node.get("content", {})
            found_title = content.get("title")
            found_year = content.get("originalReleaseYear")

            streaming = parse_offers(node)
            episode["streaming"] = streaming
            episode["lastStreamingCheck"] = time.strftime("%Y-%m-%d")

            # Show what we found
            services = [k for k, v in streaming.items() if v is True]
            if services:
                print(f"  ✓ {found_title} ({found_year}) - {', '.join(services)}")
            elif streaming["rentBuy"]:
                print(f"  ✓ {found_title} ({found_year}) - Rent/Buy: {', '.join(streaming['rentBuy'])}")
            else:
                print(f"  ✓ {found_title} ({found_year}) - Not streaming")

            updated += 1
        else:
            print(f"  ✗ Not found")
            not_found += 1

        # Rate limit
        time.sleep(0.3)

    print(f"\n--- Summary ---")
    print(f"Updated: {updated}")
    print(f"Already had data: {already_has}")
    print(f"Not found: {not_found}")

    if updated > 0:
        print(f"\nSaving to {EPISODES_PATH}...")
        with open(EPISODES_PATH, "w") as f:
            json.dump(data, f, indent=2)
        print("Done!")
    else:
        print("\nNo updates to save.")


if __name__ == "__main__":
    main()
