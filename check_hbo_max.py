#!/usr/bin/env python3

import json
import re
import urllib.request
import urllib.error
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

def title_to_slug(title):
    """Convert movie title to JustWatch slug format"""
    # Lowercase
    slug = title.lower()
    # Remove special characters, keep alphanumeric and spaces
    slug = re.sub(r'[^a-z0-9\s-]', '', slug)
    # Replace spaces with hyphens
    slug = re.sub(r'\s+', '-', slug)
    # Replace multiple hyphens with single
    slug = re.sub(r'-+', '-', slug)
    # Remove leading/trailing hyphens
    slug = slug.strip('-')
    return slug

def check_hbo_max(episode):
    """Check if HBO Max is available for a movie on JustWatch"""
    slug = title_to_slug(episode['title'])
    url = f"https://www.justwatch.com/au/movie/{slug}"

    try:
        # Create request with headers
        req = urllib.request.Request(
            url,
            headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
        )

        # Fetch the page
        with urllib.request.urlopen(req, timeout=10) as response:
            html = response.read().decode('utf-8', errors='ignore')

        # Check for HBO Max / Max in the HTML
        # Look for various patterns that might indicate Max streaming
        patterns = [
            r'hbo\s*max',
            r'hbomax',
            r'"max".*streaming',
            r'max.*provider',
            r'provider.*max',
        ]

        html_lower = html.lower()
        for pattern in patterns:
            if re.search(pattern, html_lower):
                return {
                    'id': episode['id'],
                    'title': episode['title'],
                    'year': episode['year'],
                    'url': url,
                    'hasHBOMax': True
                }

        return {
            'id': episode['id'],
            'title': episode['title'],
            'year': episode['year'],
            'url': url,
            'hasHBOMax': False
        }

    except urllib.error.HTTPError as e:
        print(f"HTTP Error for {episode['title']}: {e.code}", file=__import__('sys').stderr)
        return {
            'id': episode['id'],
            'title': episode['title'],
            'year': episode['year'],
            'url': url,
            'hasHBOMax': False,
            'error': f'HTTP {e.code}'
        }
    except Exception as e:
        print(f"Error checking {episode['title']}: {str(e)}", file=__import__('sys').stderr)
        return {
            'id': episode['id'],
            'title': episode['title'],
            'year': episode['year'],
            'url': url,
            'hasHBOMax': False,
            'error': str(e)
        }

def main():
    # Load episodes
    with open('/home/sjmur/rewatchables-aus/src/data/episodes.json', 'r') as f:
        data = json.load(f)

    episodes = data['episodes']
    print(f"Checking HBO Max availability for {len(episodes)} movies...", file=__import__('sys').stderr)

    results = []

    # Process in batches with threading for parallel requests
    batch_size = 20
    max_workers = 10

    for i in range(0, len(episodes), batch_size):
        batch = episodes[i:i+batch_size]
        batch_num = i // batch_size + 1
        total_batches = (len(episodes) + batch_size - 1) // batch_size

        print(f"\nProcessing batch {batch_num}/{total_batches} (movies {i+1}-{min(i+batch_size, len(episodes))})",
              file=__import__('sys').stderr)

        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = {executor.submit(check_hbo_max, ep): ep for ep in batch}

            for future in as_completed(futures):
                result = future.result()
                results.append(result)

                if result['hasHBOMax']:
                    print(f"  ✓ Found: {result['title']} ({result['year']})",
                          file=__import__('sys').stderr)

        # Small delay between batches to be respectful
        if i + batch_size < len(episodes):
            time.sleep(1)

    # Filter to only those with HBO Max
    with_hbo_max = [r for r in results if r['hasHBOMax']]

    print(f"\n\n{'='*60}", file=__import__('sys').stderr)
    print(f"Completed! Found {len(with_hbo_max)} movies with HBO Max out of {len(results)} total.",
          file=__import__('sys').stderr)
    print(f"{'='*60}\n", file=__import__('sys').stderr)

    # Output the IDs as JSON
    ids_with_hbo_max = [r['id'] for r in with_hbo_max]
    print(json.dumps(ids_with_hbo_max, indent=2))

    # Save full results
    with open('/tmp/hbo-max-full-results.json', 'w') as f:
        json.dump(results, f, indent=2)

    print(f"\nFull results saved to /tmp/hbo-max-full-results.json", file=__import__('sys').stderr)

    # Print summary
    print("\nMovies with HBO Max:", file=__import__('sys').stderr)
    for r in sorted(with_hbo_max, key=lambda x: x['title']):
        print(f"  - {r['title']} ({r['year']}) [{r['id']}]", file=__import__('sys').stderr)

if __name__ == '__main__':
    main()
