#!/usr/bin/env node

/**
 * Update episodes.json with Max streaming availability
 *
 * This script takes the results from check-max-streaming.js and updates
 * the episodes.json file to set hboMax: true for movies found on Max.
 *
 * Usage:
 *   node update-max-availability.js max-availability-results.json
 *
 * This will:
 * 1. Load the current episodes.json
 * 2. Load the Max availability results
 * 3. Update hboMax field for matching episodes
 * 4. Update lastStreamingCheck date
 * 5. Save backup to episodes.json.backup
 * 6. Save updated episodes.json
 */

const fs = require('fs');
const path = require('path');

// Files
const EPISODES_FILE = path.join(__dirname, 'src/data/episodes.json');
const BACKUP_FILE = path.join(__dirname, 'src/data/episodes.json.backup');

function main() {
  // Get results file from command line argument
  const resultsFile = process.argv[2];

  if (!resultsFile) {
    console.error('Usage: node update-max-availability.js <results-file>');
    console.error('');
    console.error('Example:');
    console.error('  node update-max-availability.js max-availability-results.json');
    process.exit(1);
  }

  if (!fs.existsSync(resultsFile)) {
    console.error(`Error: Results file not found: ${resultsFile}`);
    process.exit(1);
  }

  console.log('Max Availability Updater');
  console.log('='.repeat(70));
  console.log('');

  // Load results
  console.log(`Loading results from: ${resultsFile}`);
  const results = JSON.parse(fs.readFileSync(resultsFile, 'utf8'));
  console.log(`  Loaded ${results.length} results`);

  // Create a Set of episode IDs that have Max
  const idsWithMax = new Set(
    results
      .filter(r => r.hasMax)
      .map(r => r.id)
  );
  console.log(`  Found ${idsWithMax.size} episodes with Max availability`);
  console.log('');

  // Load episodes
  console.log(`Loading episodes from: ${EPISODES_FILE}`);
  const episodesData = JSON.parse(fs.readFileSync(EPISODES_FILE, 'utf8'));
  const episodes = episodesData.episodes;
  console.log(`  Loaded ${episodes.length} episodes`);
  console.log('');

  // Create backup
  console.log(`Creating backup: ${BACKUP_FILE}`);
  fs.writeFileSync(BACKUP_FILE, JSON.stringify(episodesData, null, 2));
  console.log('  ✓ Backup created');
  console.log('');

  // Update episodes
  console.log('Updating episodes...');
  let updatedCount = 0;
  let unchangedCount = 0;
  const today = new Date().toISOString().split('T')[0];

  episodes.forEach(episode => {
    const hasMax = idsWithMax.has(episode.id);
    const currentValue = episode.streaming.hboMax;

    // Update if different
    if (hasMax !== currentValue) {
      episode.streaming.hboMax = hasMax;
      episode.lastStreamingCheck = today;
      updatedCount++;

      console.log(`  ✓ Updated: ${episode.title} (${episode.year}) - hboMax: ${currentValue} → ${hasMax}`);
    } else {
      unchangedCount++;
    }
  });

  console.log('');
  console.log('Update Summary:');
  console.log(`  Updated: ${updatedCount} episodes`);
  console.log(`  Unchanged: ${unchangedCount} episodes`);
  console.log(`  Total: ${episodes.length} episodes`);
  console.log('');

  // Save updated episodes
  console.log(`Saving updated episodes to: ${EPISODES_FILE}`);
  fs.writeFileSync(EPISODES_FILE, JSON.stringify(episodesData, null, 2));
  console.log('  ✓ Episodes saved');
  console.log('');

  // Summary of Max availability
  const totalWithMax = episodes.filter(e => e.streaming.hboMax).length;
  console.log('Final Max Availability:');
  console.log(`  Episodes with Max: ${totalWithMax}/${episodes.length}`);
  console.log(`  Percentage: ${(totalWithMax / episodes.length * 100).toFixed(1)}%`);
  console.log('');

  console.log('='.repeat(70));
  console.log('✓ UPDATE COMPLETE!');
  console.log('='.repeat(70));
  console.log('');
  console.log('Next steps:');
  console.log('  1. Review the changes in episodes.json');
  console.log('  2. If satisfied, commit the changes:');
  console.log('     git add src/data/episodes.json');
  console.log('     git commit -m "Update Max streaming availability"');
  console.log('  3. If needed, restore from backup:');
  console.log(`     cp ${BACKUP_FILE} ${EPISODES_FILE}`);
  console.log('');
}

try {
  main();
} catch (error) {
  console.error('Error:', error.message);
  console.error(error.stack);
  process.exit(1);
}
