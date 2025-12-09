#!/usr/bin/env node

const fs = require('fs');
const path = require('path');
const https = require('https');

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

// Function to fetch URL and check for HBO Max
function checkHBOMax(url) {
  return new Promise((resolve, reject) => {
    https.get(url, {
      headers: {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
      }
    }, (res) => {
      let data = '';

      res.on('data', (chunk) => {
        data += chunk;
      });

      res.on('end', () => {
        // Check if HBO Max or Max appears in the response
        const hasHBOMax = data.toLowerCase().includes('hbo max') ||
                         data.toLowerCase().includes('hbomax') ||
                         data.toLowerCase().includes('"max"') ||
                         data.toLowerCase().includes('max streaming');
        resolve(hasHBOMax);
      });
    }).on('error', (err) => {
      console.error(`Error fetching ${url}: ${err.message}`);
      resolve(false); // Default to false on error
    });
  });
}

// Delay function for rate limiting
function delay(ms) {
  return new Promise(resolve => setTimeout(resolve, ms));
}

// Process movies in batches
async function processMovies() {
  const results = [];
  const batchSize = 10; // Process 10 at a time
  const delayBetweenBatches = 2000; // 2 second delay between batches

  for (let i = 0; i < data.episodes.length; i += batchSize) {
    const batch = data.episodes.slice(i, i + batchSize);
    console.error(`Processing batch ${Math.floor(i/batchSize) + 1} of ${Math.ceil(data.episodes.length/batchSize)} (movies ${i+1}-${Math.min(i+batchSize, data.episodes.length)})`);

    const promises = batch.map(async (episode) => {
      const slug = titleToSlug(episode.title);
      const url = `https://www.justwatch.com/au/movie/${slug}`;

      try {
        const hasHBO = await checkHBOMax(url);
        return {
          id: episode.id,
          title: episode.title,
          year: episode.year,
          url: url,
          hasHBOMax: hasHBO
        };
      } catch (error) {
        console.error(`Error processing ${episode.title}: ${error.message}`);
        return {
          id: episode.id,
          title: episode.title,
          year: episode.year,
          url: url,
          hasHBOMax: false,
          error: error.message
        };
      }
    });

    const batchResults = await Promise.all(promises);
    results.push(...batchResults);

    // Delay between batches to avoid rate limiting
    if (i + batchSize < data.episodes.length) {
      await delay(delayBetweenBatches);
    }
  }

  return results;
}

// Main execution
(async () => {
  console.error('Starting HBO Max availability check...\n');

  const results = await processMovies();

  // Filter to only those with HBO Max
  const withHBOMax = results.filter(r => r.hasHBOMax);

  console.error(`\n\nCompleted! Found ${withHBOMax.length} movies with HBO Max out of ${results.length} total.`);
  console.error('\nMovie IDs with HBO Max availability:');

  // Output the IDs
  console.log(JSON.stringify(withHBOMax.map(m => m.id), null, 2));

  // Also save full results to a file
  fs.writeFileSync('/tmp/hbo-max-results.json', JSON.stringify(results, null, 2));
  console.error('\nFull results saved to /tmp/hbo-max-results.json');
})();
