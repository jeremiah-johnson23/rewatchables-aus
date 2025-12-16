# The Rewatchables AU - Session Guide

**Project:** Australian streaming guide for The Rewatchables podcast
**Repo:** https://github.com/jeremiah-johnson23/rewatchables-aus
**Live Site:** https://jeremiah-johnson23.github.io/rewatchables-aus/

---

## Collaboration Identity

**AI Name:** Rog
**Human Name:** Murph

We collaborate as equals. Rog makes autonomous development decisions; Murph provides direction and reviews.

---

## Communication Shortcuts

Plain language - keep it simple:

| Signal | Meaning |
|--------|---------|
| **"go"** | Proceed with autonomy |
| **"stop"** | Hold up, let's discuss |
| **"looks good"** | Approved |
| **"fix [x]"** | Small correction needed |
| **"done"** (Rog → Murph) | Task complete, pushed |

---

## Beginning of Session

When starting a new session, Rog should:

1. Read this file (CLAUDE.md)
2. Check `git log --oneline -5` for recent changes
3. Check `git status` for uncommitted work
4. Review any open GitHub issues: `gh issue list`
5. Summarize current state before starting work

---

## End of Session

Before ending, Rog should:

1. Commit and push all changes
2. Update Session Memory below if significant work was done
3. Note any follow-up tasks needed
4. Say "done" when ready to wrap up

---

## Project Overview

### Purpose

A free, open-source website helping Australian fans of The Rewatchables podcast find where to stream the movies covered on the show. Focuses on Australian streaming services.

### Tech Stack

- **Frontend:** Vanilla JavaScript (ES6+)
- **Styling:** Tailwind CSS via CDN
- **Data:** JSON files (no backend)
- **Hosting:** GitHub Pages (free)
- **Version Control:** Git + GitHub

### File Structure

```
rewatchables-aus/
├── index.html              # Main page
├── styles.css              # Custom styles
├── app.js                  # Core functionality
├── src/data/
│   ├── episodes.json       # Episode database
│   └── streaming-services.json
├── .github/
│   ├── ISSUE_TEMPLATE/     # Community contribution templates
│   └── workflows/
│       └── deploy.yml      # GitHub Pages auto-deploy
├── CLAUDE.md               # This file
├── README.md               # Public docs
├── CONTRIBUTING.md         # Contribution guide
└── LICENSE                 # MIT
```

---

## Data Schema

### Episode Object

```json
{
  "id": "heat-1995",
  "title": "Heat",
  "year": 1995,
  "director": "Michael Mann",
  "episodeDate": "2019-12-16",
  "spotifyUrl": "https://open.spotify.com/show/1lUPomulZRPquVAOOd56EW",
  "applePodcastsUrl": "https://podcasts.apple.com/au/podcast/the-rewatchables/id1320353041",
  "hosts": ["Bill Simmons", "Chris Ryan"],
  "guests": [],
  "genres": ["Crime", "Drama", "Action"],
  "streaming": {
    "netflix": false,
    "stan": true,
    "primeVideo": true,
    "disneyPlus": false,
    "binge": false,
    "paramount": false,
    "appleTv": false,
    "hboMax": false,
    "rentBuy": ["Google Play", "Apple TV", "Amazon"]
  },
  "lastStreamingCheck": "2024-11-20",
  "editorPick": true,
  "studio": "warner-bros"
}
```

### Studios

| Studio Key | Studio Name | Native Streamer |
|------------|-------------|-----------------|
| `warner-bros` | Warner Bros. | HBO Max |
| `new-line` | New Line Cinema | HBO Max |
| `disney` | Walt Disney Pictures | Disney+ |
| `pixar` | Pixar | Disney+ |
| `marvel` | Marvel Studios | Disney+ |
| `lucasfilm` | Lucasfilm | Disney+ |
| `20th-century` | 20th Century Studios | Disney+ |
| `fox-searchlight` | Fox Searchlight | Disney+ |
| `paramount` | Paramount Pictures | Paramount+ |
| `miramax` | Miramax | Paramount+ |
| `mgm` | MGM | Prime Video |
| `amazon` | Amazon Studios | Prime Video |
| `universal` | Universal Pictures | *Licensed* |
| `sony` | Sony/Columbia | *Licensed* |
| `lionsgate` | Lionsgate | *Licensed* |
| `a24` | A24 | *Licensed* |
| `orion` | Orion Pictures | *Licensed* |
| `tristar` | TriStar Pictures | *Licensed* |
| `dreamworks` | DreamWorks | *Licensed* |
| `independent` | Independent/Other | *Licensed* |

*Licensed* = No native streamer, availability rotates between services.

### Australian Streaming Services

| Service | Key | Color |
|---------|-----|-------|
| Netflix | `netflix` | #E50914 |
| Stan | `stan` | #002B5C |
| Prime Video | `primeVideo` | #00A8E1 |
| Disney+ | `disneyPlus` | #113CCF |
| Binge | `binge` | #FF6B00 |
| Paramount+ | `paramount` | #0064FF |
| Apple TV+ | `appleTv` | #000000 |
| Max | `hboMax` | #000000 |

---

## Streaming Audit Process

### Overview

Movies fall into two categories:

1. **Native Content (279 movies)** - From studios owned by streamers. Availability is stable.
2. **Licensed Content (144 movies)** - Rotates between services. Needs monthly verification.

### Monthly Audit Procedure

Run the audit script to identify what needs checking:

```bash
# See what needs auditing
python scripts/streaming_audit.py

# View database stats
python scripts/streaming_audit.py --stats

# Check native content status
python scripts/streaming_audit.py --native

# Find movies not checked in 30+ days
python scripts/streaming_audit.py --stale 30
```

### Audit Priorities

1. **Licensed content first** - Universal, Sony, Lionsgate, A24, etc. (144 movies)
2. **Stale data** - Anything not checked in 30+ days
3. **Native content** - Only if streaming deals change (rare)

### Studio-to-Streamer Rules

Native content should *always* be available on its home service:

| Studio Owner | Native Service |
|--------------|----------------|
| Warner Bros Discovery | HBO Max |
| Disney (incl. Fox) | Disney+ |
| Paramount Global | Paramount+ |
| Amazon (MGM) | Prime Video |

### Adding Streaming Data

When checking a movie on JustWatch AU:
1. Only mark `true` for **subscription** streaming (not rent/buy)
2. Update `lastStreamingCheck` to today's date
3. Add studio field if missing: `"studio": "studio-key"`

---

## Common Tasks

### Add a New Episode

1. Edit `src/data/episodes.json`
2. Add new episode object following the schema
3. Check streaming availability on [JustWatch AU](https://www.justwatch.com/au)
4. **Add studio field** (see Studios table above)
5. Commit: `git commit -m "Add [Movie Name] episode"`

### Update Streaming Availability

1. Edit the episode in `src/data/episodes.json`
2. Update the `streaming` object
3. Update `lastStreamingCheck` date
4. Commit: `git commit -m "Update streaming for [Movie Name]"`

### Deploy Changes

Changes to `main` branch auto-deploy via GitHub Actions.

---

## Session Memory

**Last Updated:** 2024-12-17 (Session 2)

### Session 1 - Initial Setup (2024-12-05)
- Created complete site structure
- Implemented search and filtering
- Seeded database with 10 sample episodes
- Set up GitHub Pages deployment
- Created contribution templates

### Session 2 - Fix Auto-Updates (2024-12-17)
- **Diagnosed failing GitHub Action**: OMDB API key returning 401 Unauthorized
- **Fixed `add_new_episode.py`**: Removed OMDB dependency entirely (-156 lines)
  - Script now adds episodes with RSS data only (title, date, hosts)
  - No external API = reliable automation
- **Added High Fidelity (2000)** episode with full metadata
- **Fixed Apple Podcasts URL** for High Fidelity episode
- **Discussed custom domain**: `rewatchables.au` identified as preferred option

### Current State
- Site is live and functional
- Weekly auto-update workflow fixed and reliable
- Episodes in database growing (Shampoo, High Fidelity recently added)

### Next Steps
- Register `rewatchables.au` domain and configure GitHub Pages
- Continue adding episodes from podcast backlog
- Verify streaming data accuracy on JustWatch AU

---

## Framework Info

**Gordo Framework Version:** 0.8.0
**Health Check Cadence:** Every 20 sessions
**Upstream Contributions:** Enabled (with consent)

Built with [Gordo Framework](https://github.com/jkraybill/gordo-framework).
