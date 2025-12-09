#!/usr/bin/env python3
"""
Streaming Availability Audit Script for The Rewatchables AU

This script identifies which movies need their streaming availability checked
based on studio ownership. Native content (owned by streamers) is stable,
while licensed content rotates and needs monthly verification.

Usage:
    python scripts/streaming_audit.py                    # List movies needing audit
    python scripts/streaming_audit.py --stats           # Show studio/streaming stats
    python scripts/streaming_audit.py --native          # Show native content mappings
    python scripts/streaming_audit.py --stale 30        # Movies not checked in 30+ days
"""

import json
import argparse
from datetime import datetime, timedelta
from pathlib import Path

# Studio to native streamer mapping
# These studios' content is "locked" to specific streamers and rarely moves
NATIVE_STREAMING = {
    # HBO Max (Warner Bros Discovery)
    "warner-bros": "hboMax",
    "new-line": "hboMax",

    # Disney+ (Walt Disney Company)
    "disney": "disneyPlus",
    "pixar": "disneyPlus",
    "marvel": "disneyPlus",
    "lucasfilm": "disneyPlus",
    "20th-century": "disneyPlus",
    "fox-searchlight": "disneyPlus",

    # Paramount+ (Paramount Global)
    "paramount": "paramount",
    "miramax": "paramount",

    # Prime Video (Amazon)
    "mgm": "primeVideo",
    "amazon": "primeVideo",
}

# Licensed studios - content rotates between services
LICENSED_STUDIOS = [
    "universal",
    "sony",
    "lionsgate",
    "a24",
    "orion",
    "tristar",
    "dreamworks",
    "independent",
    "unknown",
]


def load_episodes():
    """Load episodes from JSON file."""
    script_dir = Path(__file__).parent
    data_file = script_dir.parent / "src" / "data" / "episodes.json"

    with open(data_file, 'r') as f:
        data = json.load(f)
    return data['episodes']


def get_stale_movies(episodes, days=30):
    """Get movies that haven't been checked in X days."""
    cutoff = datetime.now() - timedelta(days=days)
    stale = []

    for ep in episodes:
        check_date_str = ep.get('lastStreamingCheck', '2020-01-01')
        try:
            check_date = datetime.strptime(check_date_str, '%Y-%m-%d')
            if check_date < cutoff:
                stale.append({
                    'id': ep['id'],
                    'title': ep['title'],
                    'studio': ep.get('studio', 'unknown'),
                    'last_check': check_date_str,
                    'days_old': (datetime.now() - check_date).days
                })
        except ValueError:
            stale.append({
                'id': ep['id'],
                'title': ep['title'],
                'studio': ep.get('studio', 'unknown'),
                'last_check': 'invalid',
                'days_old': 999
            })

    return sorted(stale, key=lambda x: -x['days_old'])


def get_licensed_content(episodes):
    """Get movies from licensed studios that need regular checking."""
    licensed = []

    for ep in episodes:
        studio = ep.get('studio', 'unknown')
        if studio in LICENSED_STUDIOS:
            licensed.append({
                'id': ep['id'],
                'title': ep['title'],
                'year': ep['year'],
                'studio': studio,
                'last_check': ep.get('lastStreamingCheck', 'never'),
            })

    return licensed


def get_native_content(episodes):
    """Get movies from studios with native streamers."""
    native = []

    for ep in episodes:
        studio = ep.get('studio', 'unknown')
        if studio in NATIVE_STREAMING:
            native_service = NATIVE_STREAMING[studio]
            has_native = ep['streaming'].get(native_service, False)
            native.append({
                'id': ep['id'],
                'title': ep['title'],
                'studio': studio,
                'native_service': native_service,
                'has_native': has_native,
            })

    return native


def get_stats(episodes):
    """Get statistics about the database."""
    stats = {
        'total': len(episodes),
        'by_studio': {},
        'by_service': {
            'netflix': 0,
            'stan': 0,
            'primeVideo': 0,
            'disneyPlus': 0,
            'binge': 0,
            'paramount': 0,
            'appleTv': 0,
            'hboMax': 0,
        },
        'native_count': 0,
        'licensed_count': 0,
    }

    for ep in episodes:
        studio = ep.get('studio', 'unknown')
        stats['by_studio'][studio] = stats['by_studio'].get(studio, 0) + 1

        if studio in NATIVE_STREAMING:
            stats['native_count'] += 1
        else:
            stats['licensed_count'] += 1

        for service, available in ep['streaming'].items():
            if service != 'rentBuy' and available:
                stats['by_service'][service] = stats['by_service'].get(service, 0) + 1

    return stats


def print_audit_list(episodes):
    """Print list of movies needing audit (licensed content only)."""
    licensed = get_licensed_content(episodes)
    stale = get_stale_movies([ep for ep in episodes if ep.get('studio', 'unknown') in LICENSED_STUDIOS], days=30)

    print("=" * 60)
    print("MONTHLY STREAMING AUDIT - LICENSED CONTENT")
    print("=" * 60)
    print(f"\nTotal licensed movies: {len(licensed)}")
    print(f"Stale (30+ days): {len(stale)}")
    print("\n--- Priority Audit List (oldest first) ---\n")

    for movie in stale[:50]:  # Show top 50
        print(f"  [{movie['days_old']:3d}d] {movie['title']} ({movie['studio']})")

    if len(stale) > 50:
        print(f"\n  ... and {len(stale) - 50} more")


def print_stats(episodes):
    """Print database statistics."""
    stats = get_stats(episodes)

    print("=" * 60)
    print("DATABASE STATISTICS")
    print("=" * 60)
    print(f"\nTotal movies: {stats['total']}")
    print(f"Native content (stable): {stats['native_count']}")
    print(f"Licensed content (needs audit): {stats['licensed_count']}")

    print("\n--- By Studio ---")
    for studio, count in sorted(stats['by_studio'].items(), key=lambda x: -x[1]):
        native = "→ " + NATIVE_STREAMING.get(studio, "licensed")
        print(f"  {studio:20s}: {count:3d}  {native}")

    print("\n--- By Streaming Service ---")
    for service, count in sorted(stats['by_service'].items(), key=lambda x: -x[1]):
        print(f"  {service:15s}: {count:3d} movies")


def print_native_content(episodes):
    """Print native content mapping status."""
    native = get_native_content(episodes)

    print("=" * 60)
    print("NATIVE CONTENT STATUS")
    print("=" * 60)
    print("\nThese movies are from studios owned by streamers.")
    print("Their availability should be stable.\n")

    missing_native = [m for m in native if not m['has_native']]

    if missing_native:
        print(f"⚠️  {len(missing_native)} movies missing from their native service:\n")
        for movie in missing_native[:30]:
            print(f"  {movie['title']} ({movie['studio']}) → should be on {movie['native_service']}")
    else:
        print("✓ All native content correctly tagged!")


def main():
    parser = argparse.ArgumentParser(description='Streaming availability audit tool')
    parser.add_argument('--stats', action='store_true', help='Show database statistics')
    parser.add_argument('--native', action='store_true', help='Show native content status')
    parser.add_argument('--stale', type=int, metavar='DAYS', help='Show movies not checked in X days')

    args = parser.parse_args()
    episodes = load_episodes()

    if args.stats:
        print_stats(episodes)
    elif args.native:
        print_native_content(episodes)
    elif args.stale:
        stale = get_stale_movies(episodes, days=args.stale)
        print(f"\n{len(stale)} movies not checked in {args.stale}+ days:\n")
        for movie in stale[:50]:
            print(f"  [{movie['days_old']:3d}d] {movie['title']} ({movie['studio']})")
    else:
        print_audit_list(episodes)


if __name__ == '__main__':
    main()
