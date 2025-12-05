# Contributing to The Rewatchables AU

Thanks for your interest in contributing! This guide will help you get started.

---

## Ways to Contribute

### 1. Report Streaming Updates (Easiest)

Streaming availability changes frequently. Help us keep the database accurate:

1. Go to [Issues](https://github.com/jeremiah-johnson23/rewatchables-aus/issues)
2. Click "New Issue"
3. Select "Streaming Update"
4. Fill in the details

**Tip:** Check [JustWatch AU](https://www.justwatch.com/au) to verify current availability.

### 2. Request New Episodes

Missing an episode? Let us know:

1. Go to [Issues](https://github.com/jeremiah-johnson23/rewatchables-aus/issues)
2. Click "New Issue"
3. Select "New Episode Request"
4. Fill in as much detail as you can

### 3. Submit a Pull Request (For developers)

Want to add data yourself? Here's how:

#### Setup

```bash
# Fork and clone the repo
git clone https://github.com/YOUR-USERNAME/rewatchables-aus.git
cd rewatchables-aus

# Create a branch for your changes
git checkout -b add-episode-moviename
```

#### Adding an Episode

1. Open `src/data/episodes.json`
2. Add a new episode object following this schema:

```json
{
  "id": "movie-title-year",
  "title": "Movie Title",
  "year": 1999,
  "director": "Director Name",
  "episodeDate": "YYYY-MM-DD",
  "spotifyUrl": "https://open.spotify.com/episode/...",
  "hosts": ["Bill Simmons", "Chris Ryan"],
  "guests": [],
  "hallOfFame": false,
  "genres": ["Genre1", "Genre2"],
  "streaming": {
    "netflix": false,
    "stan": false,
    "primeVideo": false,
    "disneyPlus": false,
    "binge": false,
    "paramount": false,
    "appleTv": false,
    "rentBuy": ["Google Play", "Apple TV", "Amazon"]
  },
  "lastStreamingCheck": "YYYY-MM-DD",
  "communityRating": {
    "average": 0,
    "votes": 0
  }
}
```

#### Updating Streaming Availability

1. Open `src/data/episodes.json`
2. Find the episode by `id`
3. Update the `streaming` object
4. Update `lastStreamingCheck` to today's date

#### Submit Your Changes

```bash
# Commit your changes
git add .
git commit -m "Add [Movie Name] episode"

# Push to your fork
git push origin add-episode-moviename
```

Then open a Pull Request on GitHub.

---

## Data Guidelines

### Episode IDs

Use lowercase, hyphenated format: `movie-title-year`
- `heat-1995`
- `the-godfather-1972`
- `die-hard-1988`

### Episode Dates

Use ISO format: `YYYY-MM-DD`

### Spotify URLs

Find the episode on Spotify, click share, and copy the link.

### Streaming Services

Only set a service to `true` if the movie is included with a subscription (not just available to rent/buy on that platform).

### Genres

Use common genre names. Examples:
- Action, Adventure, Animation, Biography, Comedy, Crime, Documentary, Drama, Family, Fantasy, History, Horror, Music, Mystery, Romance, Sci-Fi, Sport, Thriller, War, Western

### Community Ratings

- New episodes start with `"average": 0, "votes": 0`
- Ratings are updated through a separate process

---

## Code Style

- Use 2 spaces for indentation in JSON
- Keep arrays on single lines when short
- Sort episodes by `id` alphabetically (optional but appreciated)

---

## Questions?

Open an issue with the "question" label and we'll help you out.

---

Thanks for helping make this resource better for Australian Rewatchables fans! 🎬🇦🇺
