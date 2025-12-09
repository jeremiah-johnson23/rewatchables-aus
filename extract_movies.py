#!/usr/bin/env python3
import json

with open('/home/sjmur/rewatchables-aus/src/data/episodes.json', 'r') as f:
    data = json.load(f)

movies = data['episodes'][150:250]

# Create simplified output
output = []
for i, movie in enumerate(movies, start=151):
    # Create slug for JustWatch (simple version - lowercase, replace spaces with hyphens)
    title_slug = movie['title'].lower().replace(' ', '-').replace(':', '').replace("'", '').replace('.', '')
    title_slug = title_slug.replace('(', '').replace(')', '').replace(',', '').replace('--', '-')

    current_services = []
    streaming = movie.get('streaming', {})
    if streaming.get('netflix'): current_services.append('netflix')
    if streaming.get('stan'): current_services.append('stan')
    if streaming.get('primeVideo'): current_services.append('primeVideo')
    if streaming.get('disneyPlus'): current_services.append('disneyPlus')
    if streaming.get('binge'): current_services.append('binge')
    if streaming.get('paramount'): current_services.append('paramount')
    if streaming.get('appleTv'): current_services.append('appleTv')
    if streaming.get('hboMax'): current_services.append('hboMax')

    output.append({
        'index': i,
        'id': movie['id'],
        'title': movie['title'],
        'year': movie['year'],
        'justwatch_url': f"https://www.justwatch.com/au/movie/{title_slug}",
        'current_services': current_services,
        'last_check': movie.get('lastStreamingCheck', 'Never')
    })

# Save to JSON for reference
with open('/home/sjmur/rewatchables-aus/movies_151_250.json', 'w') as f:
    json.dump(output, f, indent=2)

# Print summary
print(f"Extracted {len(output)} movies (151-250)")
print(f"\nFirst 5:")
for m in output[:5]:
    print(f"  {m['index']}. {m['title']} ({m['year']}) - {m['id']}")
    print(f"     Current: {', '.join(m['current_services']) if m['current_services'] else 'None'}")

print(f"\nSaved to movies_151_250.json")
