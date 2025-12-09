# Quick Start: Check Max Availability for All 423 Movies

## TL;DR - Just Run This

```bash
cd /home/sjmur/rewatchables-aus
node check-max-streaming.js
```

Wait 5-7 minutes, then you'll have your results.

---

## What You Get

After running the script, you'll have:

1. **`max-availability-results.json`** - Full details for all 423 movies
2. **Console output** - List of episode IDs with Max (JSON array)

---

## Full Workflow (Step by Step)

### Step 1: Check Max Availability (5-7 minutes)

```bash
cd /home/sjmur/rewatchables-aus
node check-max-streaming.js > max-episode-ids.json
```

This will:
- Check all 423 movies on JustWatch AU
- Show progress in real-time
- Save episode IDs to `max-episode-ids.json`
- Save full results to `max-availability-results.json`

### Step 2: Review Results

```bash
# See how many movies have Max
cat max-episode-ids.json | jq '. | length'

# View the episode IDs
cat max-episode-ids.json | jq

# See detailed results for movies with Max
cat max-availability-results.json | jq '.[] | select(.hasMax==true)'
```

### Step 3: Update episodes.json (OPTIONAL - Automated)

```bash
# This will automatically update episodes.json
node update-max-availability.js max-availability-results.json
```

This will:
- Create a backup: `src/data/episodes.json.backup`
- Update `hboMax` field for all episodes
- Update `lastStreamingCheck` dates
- Show summary of changes

### Step 4: Commit Changes

```bash
git add src/data/episodes.json
git commit -m "Update Max streaming availability for all 423 episodes"
git push
```

---

## Files Created

All files are in `/home/sjmur/rewatchables-aus/`:

| File | Purpose |
|------|---------|
| `check-max-streaming.js` | Main script to check JustWatch |
| `check_hbo_max.py` | Python alternative |
| `update-max-availability.js` | Auto-update episodes.json |
| `RUN_MAX_CHECK.sh` | Easy launcher shell script |
| `CHECK_MAX_README.md` | Full documentation |
| `MAX_CHECK_SUMMARY.md` | Summary guide |
| `QUICK_START.md` | This file |

---

## Output Files (Created When You Run)

| File | Content |
|------|---------|
| `max-episode-ids.json` | Array of episode IDs with Max |
| `max-availability-results.json` | Full details for all movies |
| `src/data/episodes.json.backup` | Backup before updates |

---

## Example Output

### While Running:
```
[1/29] Processing movies 1-15...
  ✓ FOUND: Rocky II (1979)
  Progress: 15/423 checked, 1 with Max

[2/29] Processing movies 16-30...
  ✓ FOUND: The Sting (1973)
  Progress: 30/423 checked, 2 with Max
```

### Final Output:
```
======================================================================
COMPLETE!
Total movies checked: 423
Movies with Max: 87
Success rate: 423/423
======================================================================

[
  "rocky-ii",
  "the-sting",
  "airplane",
  ...
]
```

---

## Troubleshooting

### Script won't run
```bash
# Check Node.js is installed
node --version  # Should be v12 or higher

# If not installed
sudo apt install nodejs  # Ubuntu/Debian
brew install node        # macOS
```

### Too slow / Rate limited
Edit `check-max-streaming.js` and change:
```javascript
delayBetweenBatches: 5000,  // Increase from 2000 to 5000
batchSize: 10,              // Decrease from 15 to 10
```

### Results seem wrong
- Manually check a few movies on https://www.justwatch.com/au
- Review `max-availability-results.json` for errors
- Some movies might have different slugs than expected

---

## What the Script Does

1. **Reads** all 423 movies from `src/data/episodes.json`
2. **Converts** titles to JustWatch slugs (e.g., "The Dark Knight" → "the-dark-knight")
3. **Fetches** each movie's page from JustWatch AU
4. **Searches** for Max/HBO Max in the HTML
5. **Collects** results and outputs episode IDs

---

## Manual Update (Alternative to Step 3)

If you prefer to update episodes.json manually:

1. Get the episode IDs from `max-episode-ids.json`
2. For each ID in the list, find it in `episodes.json`
3. Set `"hboMax": true` in the `streaming` object
4. Update `"lastStreamingCheck"` to today's date

---

## Notes

- **Runtime:** ~5-7 minutes for all 423 movies
- **Rate limiting:** Built-in 2-second delays between batches
- **Error handling:** Timeouts and network errors handled gracefully
- **Respectful:** Won't hammer JustWatch servers
- **Accurate:** Checks the actual JustWatch AU pages
- **Flexible:** Easily customizable if needed

---

## One-Line Command (Everything)

If you want to do it all in one go:

```bash
cd /home/sjmur/rewatchables-aus && \
node check-max-streaming.js > max-episode-ids.json && \
node update-max-availability.js max-availability-results.json && \
echo "Done! Check src/data/episodes.json"
```

---

## Need Help?

1. Check `CHECK_MAX_README.md` for full documentation
2. Check `MAX_CHECK_SUMMARY.md` for detailed explanations
3. Review the scripts - they're well-commented
4. Open an issue on GitHub

---

## Ready?

Just run:

```bash
cd /home/sjmur/rewatchables-aus
node check-max-streaming.js
```

That's it! The script will handle everything else.
