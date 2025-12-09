# HBO Max / Max Streaming Availability Checker

This directory contains scripts to check JustWatch Australia for Max (formerly HBO Max) streaming availability for all movies in the Rewatchables episodes database.

## Available Scripts

### 1. Node.js Version (Recommended)
**File:** `check-max-streaming.js`

**Usage:**
```bash
node check-max-streaming.js > max-episode-ids.json 2>&1
```

**Features:**
- Processes all 423 movies in batches of 15
- 2-second delay between batches to avoid rate limiting
- Parallel requests within each batch for speed
- Detailed progress logging to stderr
- Final JSON array of episode IDs to stdout
- Full results saved to `max-availability-results.json`

**Output:**
- **stdout:** JSON array of episode IDs with Max availability
- **stderr:** Progress logs and summary
- **File:** `max-availability-results.json` - detailed results for all movies

**Expected Runtime:** ~5-7 minutes for 423 movies

---

### 2. Python Version (Alternative)
**File:** `check_hbo_max.py`

**Usage:**
```bash
chmod +x check_hbo_max.py
python3 check_hbo_max.py > max-episode-ids.json 2>&1
```

**Features:**
- Similar functionality to Node.js version
- Uses threading for parallel requests
- Batch processing with rate limiting

---

## How It Works

### 1. Slug Generation
Converts movie titles to JustWatch URL format:
- `"The Dark Knight"` → `"the-dark-knight"`
- `"Star Wars: A New Hope"` → `"star-wars-a-new-hope"`

### 2. URL Construction
```
https://www.justwatch.com/au/movie/{slug}
```

### 3. Max Detection
Searches the HTML for patterns indicating Max streaming:
- "HBO Max"
- "hbomax"
- JSON properties with "max"
- Provider data with "max"

### 4. Result Collection
Each movie result includes:
```json
{
  "id": "the-dark-knight",
  "title": "The Dark Knight",
  "year": 2008,
  "slug": "the-dark-knight",
  "url": "https://www.justwatch.com/au/movie/the-dark-knight",
  "hasMax": true,
  "status": "success",
  "statusCode": 200
}
```

---

## Quick Start

### Run the check:
```bash
# Node.js (recommended)
node check-max-streaming.js

# Or Python
python3 check_hbo_max.py
```

### The script will:
1. Load all 423 episodes from `src/data/episodes.json`
2. Check each movie on JustWatch AU
3. Report progress to the console
4. Save results to `max-availability-results.json`
5. Output episode IDs with Max to stdout

### Example Output:
```
[69/70] Processing movies 406-420...
  ✓ FOUND: The Matrix (1999)
  ✓ FOUND: Goodfellas (1990)
  Progress: 420/423 checked, 87 with Max

======================================================================
COMPLETE!
Total movies checked: 423
Movies with Max: 87
Success rate: 420/423
======================================================================

[
  "rocky-ii",
  "the-matrix",
  "goodfellas",
  ...
]
```

---

## Updating episodes.json

After running the script, you can update the episodes.json file manually or create a script to update the `hboMax` field based on the results.

### Manual Update Example:
If `rocky-ii` is in the output list, update its entry:
```json
{
  "id": "rocky-ii",
  "title": "Rocky II",
  "streaming": {
    "hboMax": true  ← Update this
  },
  "lastStreamingCheck": "2025-12-09"  ← Update date
}
```

---

## Troubleshooting

### Rate Limiting
If you get rate limited:
- Increase `delayBetweenBatches` (e.g., to 5000ms)
- Decrease `batchSize` (e.g., to 10)

### Timeouts
If many requests timeout:
- Increase `requestTimeout` (e.g., to 15000ms)
- Check your internet connection

### False Negatives
Some movies might not be detected if:
- The JustWatch slug is different than expected
- The movie title has special formatting
- JustWatch AU doesn't have the movie

Check `max-availability-results.json` for the full results and manually verify any suspicious cases.

---

## Notes

- The script respects rate limiting with delays between batches
- JustWatch URLs are case-insensitive but we use lowercase by convention
- Some movies may have multiple entries on JustWatch (sequels, remakes, etc.)
- Results are based on the HTML content and may need verification
- Max availability can change over time - re-run periodically

---

## Contact

For issues or questions about these scripts, check the main project README or open an issue on GitHub.
