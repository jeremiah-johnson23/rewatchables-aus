#!/usr/bin/env python3
"""
Audit script for movies 151-250 from episodes.json
Extracts movie data for manual checking against JustWatch AU
"""

import json

# Read episodes.json
with open('/home/sjmur/rewatchables-aus/src/data/episodes.json', 'r') as f:
    data = json.load(f)

# Get movies 151-250 (indices 150-249)
movies = data['episodes'][150:250]

print(f"Total movies to check: {len(movies)}\n")
print("="*80)

# Output each movie for checking
for i, movie in enumerate(movies, start=151):
    print(f"\n#{i}: {movie['title']} ({movie['year']})")
    print(f"ID: {movie['id']}")

    # Get current streaming status
    current_services = []
    streaming = movie.get('streaming', {})

    if streaming.get('netflix'): current_services.append('Netflix')
    if streaming.get('stan'): current_services.append('Stan')
    if streaming.get('primeVideo'): current_services.append('Prime Video')
    if streaming.get('disneyPlus'): current_services.append('Disney+')
    if streaming.get('binge'): current_services.append('Binge')
    if streaming.get('paramount'): current_services.append('Paramount+')
    if streaming.get('appleTv'): current_services.append('Apple TV+')
    if streaming.get('hboMax'): current_services.append('HBO Max')

    print(f"Current Streaming: {', '.join(current_services) if current_services else 'None'}")
    print(f"Last Check: {movie.get('lastStreamingCheck', 'Never')}")
    print("-"*80)
