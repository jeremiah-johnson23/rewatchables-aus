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
  "spotifyUrl": "https://open.spotify.com/episode/...",
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
    "rentBuy": ["Google Play", "Apple TV", "Amazon"]
  },
  "lastStreamingCheck": "2024-11-20",
  "communityRating": {
    "average": 4.8,
    "votes": 142
  }
}
```

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

---

## Common Tasks

### Add a New Episode

1. Edit `src/data/episodes.json`
2. Add new episode object following the schema
3. Check streaming availability on [JustWatch AU](https://www.justwatch.com/au)
4. Commit: `git commit -m "Add [Movie Name] episode"`

### Update Streaming Availability

1. Edit the episode in `src/data/episodes.json`
2. Update the `streaming` object
3. Update `lastStreamingCheck` date
4. Commit: `git commit -m "Update streaming for [Movie Name]"`

### Deploy Changes

Changes to `main` branch auto-deploy via GitHub Actions.

---

## Session Memory

**Last Updated:** 2024-12-05 (Session 1)

### Session 1 - Initial Setup
- Created complete site structure
- Implemented search and filtering
- Seeded database with 10 sample episodes
- Set up GitHub Pages deployment
- Created contribution templates

### Current State
- Site is live and functional
- 10 episodes in database
- Search, filter, sort all working

### Next Steps
- Add more episodes from podcast backlog
- Verify streaming data accuracy
- Gather community feedback

---

## Framework Info

**Gordo Framework Version:** 0.8.0
**Health Check Cadence:** Every 20 sessions
**Upstream Contributions:** Enabled (with consent)

Built with [Gordo Framework](https://github.com/jkraybill/gordo-framework).
