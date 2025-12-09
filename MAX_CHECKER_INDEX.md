# Max Streaming Availability Checker - File Index

## Quick Start

**Want to just run it?** → Read [`QUICK_START.md`](QUICK_START.md)

**Want to understand everything?** → Read [`MAX_CHECK_SUMMARY.md`](MAX_CHECK_SUMMARY.md)

**Need full documentation?** → Read [`CHECK_MAX_README.md`](CHECK_MAX_README.md)

---

## All Files Created

### 🎬 Main Scripts

| File | Type | Purpose | How to Run |
|------|------|---------|------------|
| **`check-max-streaming.js`** | Node.js | PRIMARY - Check Max availability for all 423 movies | `node check-max-streaming.js` |
| **`check_hbo_max.py`** | Python | Alternative Python version | `python3 check_hbo_max.py` |
| **`update-max-availability.js`** | Node.js | Auto-update episodes.json with results | `node update-max-availability.js max-availability-results.json` |

### 🚀 Launchers

| File | Purpose |
|------|---------|
| **`RUN_MAX_CHECK.sh`** | Easy launcher with prompts and progress | `./RUN_MAX_CHECK.sh` |

### 📚 Documentation

| File | What It Contains |
|------|------------------|
| **`QUICK_START.md`** | TL;DR - Just the commands you need |
| **`MAX_CHECK_SUMMARY.md`** | Complete overview, what/why/how |
| **`CHECK_MAX_README.md`** | Full documentation with troubleshooting |
| **`MAX_CHECKER_INDEX.md`** | This file - index of all files |

### 🗑️ Legacy/Intermediate Files

| File | Status | Note |
|------|--------|------|
| `check-hbo-max.js` | Superseded | Use `check-max-streaming.js` instead |
| `check-hbo-availability.js` | Superseded | Use `check-max-streaming.js` instead |

---

## Recommended Workflow

### 1️⃣ First Time - Read This
Start with [`QUICK_START.md`](QUICK_START.md) - it has everything you need in simple steps.

### 2️⃣ Run the Check
```bash
node check-max-streaming.js
```

### 3️⃣ Get Your Results
- Console output: Episode IDs as JSON array
- File: `max-availability-results.json` with full details

### 4️⃣ Update episodes.json (Optional)
```bash
node update-max-availability.js max-availability-results.json
```

### 5️⃣ Commit Changes
```bash
git add src/data/episodes.json
git commit -m "Update Max streaming availability"
```

---

## File Sizes

- **`check-max-streaming.js`**: ~6 KB - Main script
- **`check_hbo_max.py`**: ~5 KB - Python alternative
- **`update-max-availability.js`**: ~4 KB - Updater script
- **`episodes.json`**: ~424 KB - Your data (423 movies)

---

## Output Files (Generated When You Run)

These files will be created after running the scripts:

| File | Size | Content |
|------|------|---------|
| `max-episode-ids.json` | ~3 KB | Array of episode IDs with Max |
| `max-availability-results.json` | ~50 KB | Full details for all 423 movies |
| `src/data/episodes.json.backup` | ~424 KB | Backup before updating |

---

## One Command to Rule Them All

Want to do everything in one go?

```bash
cd /home/sjmur/rewatchables-aus && \
node check-max-streaming.js > max-episode-ids.json && \
echo "Results saved! Found $(cat max-episode-ids.json | jq '. | length') movies with Max."
```

---

## What Happens

```
┌─────────────────────────────────────────────┐
│  1. Load episodes.json (423 movies)         │
└────────────────┬────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────┐
│  2. Convert titles to JustWatch slugs       │
│     "The Dark Knight" → "the-dark-knight"   │
└────────────────┬────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────┐
│  3. Fetch each movie from JustWatch AU      │
│     https://justwatch.com/au/movie/[slug]   │
│     (15 at a time, with 2s delays)          │
└────────────────┬────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────┐
│  4. Search HTML for Max streaming           │
│     Look for: HBO Max, hbomax, "max", etc.  │
└────────────────┬────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────┐
│  5. Collect results                         │
│     hasMax: true/false for each movie       │
└────────────────┬────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────┐
│  6. Output episode IDs with Max             │
│     ["rocky-ii", "the-sting", ...]          │
└─────────────────────────────────────────────┘
```

---

## Tech Details

- **Language**: Node.js (v12+) or Python 3
- **Dependencies**: None! Uses built-in `https` module
- **Rate Limiting**: 2-second delays between batches
- **Batch Size**: 15 movies per batch
- **Total Batches**: 29 batches
- **Est. Runtime**: 5-7 minutes
- **Success Rate**: Should be 100% unless network issues

---

## Customization

Edit the `CONFIG` section in `check-max-streaming.js`:

```javascript
const CONFIG = {
  batchSize: 15,              // Movies per batch
  delayBetweenBatches: 2000,  // Delay in milliseconds
  requestTimeout: 10000,      // Timeout per request
};
```

---

## Need Help?

1. **Quick question?** → Check [`QUICK_START.md`](QUICK_START.md)
2. **Understanding?** → Check [`MAX_CHECK_SUMMARY.md`](MAX_CHECK_SUMMARY.md)
3. **Deep dive?** → Check [`CHECK_MAX_README.md`](CHECK_MAX_README.md)
4. **Technical issue?** → Check the script comments
5. **Still stuck?** → Open a GitHub issue

---

## Status

✅ All scripts created and ready
✅ All documentation written
✅ All files tested (syntax-wise)
🔲 Waiting for you to run them

---

## What You Need to Do

**Just one command:**

```bash
cd /home/sjmur/rewatchables-aus && node check-max-streaming.js
```

That's it! The script handles the rest.

---

**Created**: 2025-12-09
**For**: Checking Max streaming availability on JustWatch AU
**Movies**: 423 from The Rewatchables podcast
**Ready**: Yes, go for it!
