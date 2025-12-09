#!/usr/bin/env node

/**
 * HBO Max / Max Streaming Availability Checker for JustWatch Australia
 *
 * This script checks all movies in episodes.json against JustWatch AU
 * to determine if they're available on Max (formerly HBO Max).
 *
 * Usage: node check-max-streaming.js
 * Output: JSON array of episode IDs that have Max availability
 */

const fs = require('fs');
const path = require('path');
const https = require('https');

// Configuration
const CONFIG = {
  episodesFile: path.join(__dirname, 'src/data/episodes.json'),
  outputFile: path.join(__dirname, 'max-availability-results.json'),
  batchSize: 15,           // Process 15 movies at a time
  delayBetweenBatches: 2000, // 2 seconds between batches
  requestTimeout: 10000,   // 10 second timeout per request
};

/**
 * Convert movie title to JustWatch URL slug
 * e.g., "The Dark Knight" -> "the-dark-knight"
 */
function titleToSlug(title) {
  return title
    .toLowerCase()
    .replace(/[^a-z0-9\s-]/g, '') // Remove special characters
    .replace(/\s+/g, '-')         // Replace spaces with hyphens
    .replace(/-+/g, '-')          // Collapse multiple hyphens
    .replace(/^-|-$/g, '');       // Remove leading/trailing hyphens
}

/**
 * Fetch JustWatch page and check for Max streaming availability
 */
function checkMaxAvailability(episode) {
  return new Promise((resolve) => {
    const slug = titleToSlug(episode.title);
    const url = `https://www.justwatch.com/au/movie/${slug}`;

    const options = {
      headers: {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-AU,en;q=0.9',
      },
      timeout: CONFIG.requestTimeout,
    };

    const req = https.get(url, options, (res) => {
      let data = '';

      res.on('data', (chunk) => {
        data += chunk;
      });

      res.on('end', () => {
        // Check for Max/HBO Max in the HTML content
        // JustWatch typically includes provider names in various formats
        const html = data.toLowerCase();

        const patterns = [
          /\bhbo\s*max\b/i,
          /\bhbomax\b/i,
          /\"max\"/i,              // JSON property with "max"
          /provider.*max/i,
          /max.*provider/i,
          /data-provider.*max/i,
          /streamingchart.*max/i,
        ];

        const hasMax = patterns.some(pattern => pattern.test(data));

        resolve({
          id: episode.id,
          title: episode.title,
          year: episode.year,
          slug: slug,
          url: url,
          hasMax: hasMax,
          status: 'success',
          statusCode: res.statusCode,
        });
      });
    });

    req.on('error', (error) => {
      console.error(`Error fetching ${episode.title}: ${error.message}`);
      resolve({
        id: episode.id,
        title: episode.title,
        year: episode.year,
        slug: slug,
        url: url,
        hasMax: false,
        status: 'error',
        error: error.message,
      });
    });

    req.on('timeout', () => {
      req.destroy();
      console.error(`Timeout fetching ${episode.title}`);
      resolve({
        id: episode.id,
        title: episode.title,
        year: episode.year,
        slug: slug,
        url: url,
        hasMax: false,
        status: 'timeout',
      });
    });
  });
}

/**
 * Delay helper for rate limiting
 */
function delay(ms) {
  return new Promise(resolve => setTimeout(resolve, ms));
}

/**
 * Process all episodes in batches
 */
async function processAllEpisodes(episodes) {
  const results = [];
  const totalBatches = Math.ceil(episodes.length / CONFIG.batchSize);

  console.error('Starting Max availability check...');
  console.error(`Total movies: ${episodes.length}`);
  console.error(`Batch size: ${CONFIG.batchSize}`);
  console.error(`Total batches: ${totalBatches}\n`);

  for (let i = 0; i < episodes.length; i += CONFIG.batchSize) {
    const batch = episodes.slice(i, i + CONFIG.batchSize);
    const batchNum = Math.floor(i / CONFIG.batchSize) + 1;
    const movieRange = `${i + 1}-${Math.min(i + CONFIG.batchSize, episodes.length)}`;

    console.error(`\n[${ batchNum}/${totalBatches}] Processing movies ${movieRange}...`);

    // Process batch in parallel
    const batchPromises = batch.map(episode => checkMaxAvailability(episode));
    const batchResults = await Promise.all(batchPromises);

    // Log any found matches
    batchResults.forEach(result => {
      if (result.hasMax) {
        console.error(`  ✓ FOUND: ${result.title} (${result.year})`);
      }
    });

    results.push(...batchResults);

    // Progress update
    const foundSoFar = results.filter(r => r.hasMax).length;
    console.error(`  Progress: ${results.length}/${episodes.length} checked, ${foundSoFar} with Max`);

    // Delay between batches (except for the last one)
    if (i + CONFIG.batchSize < episodes.length) {
      await delay(CONFIG.delayBetweenBatches);
    }
  }

  return results;
}

/**
 * Main execution
 */
async function main() {
  try {
    // Load episodes
    console.error(`Reading episodes from ${CONFIG.episodesFile}...`);
    const rawData = fs.readFileSync(CONFIG.episodesFile, 'utf8');
    const data = JSON.parse(rawData);
    const episodes = data.episodes;

    console.error(`Loaded ${episodes.length} episodes\n`);

    // Process all episodes
    const results = await processAllEpisodes(episodes);

    // Filter to only those with Max
    const withMax = results.filter(r => r.hasMax);
    const episodeIdsWithMax = withMax.map(r => r.id);

    // Summary
    console.error('\n' + '='.repeat(70));
    console.error(`COMPLETE!`);
    console.error(`Total movies checked: ${results.length}`);
    console.error(`Movies with Max: ${withMax.length}`);
    console.error(`Success rate: ${results.filter(r => r.status === 'success').length}/${results.length}`);
    console.error('='.repeat(70));

    // Save detailed results
    fs.writeFileSync(CONFIG.outputFile, JSON.stringify(results, null, 2));
    console.error(`\nDetailed results saved to: ${CONFIG.outputFile}`);

    // Output the episode IDs (main output)
    console.log('\n' + JSON.stringify(episodeIdsWithMax, null, 2));

    // Print list of movies found
    if (withMax.length > 0) {
      console.error('\nMovies available on Max:');
      withMax
        .sort((a, b) => a.title.localeCompare(b.title))
        .forEach(movie => {
          console.error(`  - ${movie.title} (${movie.year}) [${movie.id}]`);
        });
    }

    process.exit(0);
  } catch (error) {
    console.error(`Fatal error: ${error.message}`);
    console.error(error.stack);
    process.exit(1);
  }
}

// Run the script
main();
