#!/usr/bin/env node

const fs = require('fs');
const path = require('path');

// Read episodes file
const episodesPath = path.join(__dirname, 'src/data/episodes.json');
const data = JSON.parse(fs.readFileSync(episodesPath, 'utf8'));

// Function to convert movie title to JustWatch slug
function titleToSlug(title) {
  return title
    .toLowerCase()
    .replace(/[^a-z0-9\s-]/g, '') // Remove special characters
    .replace(/\s+/g, '-')         // Replace spaces with hyphens
    .replace(/-+/g, '-')          // Replace multiple hyphens with single
    .trim();
}

// Generate list of all movies with their JustWatch URLs
const movies = data.episodes.map(episode => ({
  id: episode.id,
  title: episode.title,
  year: episode.year,
  slug: titleToSlug(episode.title),
  url: `https://www.justwatch.com/au/movie/${titleToSlug(episode.title)}`
}));

console.log(JSON.stringify(movies, null, 2));
console.log(`\n\nTotal movies to check: ${movies.length}`);
