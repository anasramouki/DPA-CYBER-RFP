import { orchestrator } from '../src/scrapers/orchestrator';

async function main() {
  console.log('--- Testing Scraping Orchestrator on Live Database ---');
  const result = await orchestrator.runAll();
  console.log(`Scraped ${result.totalSources} sources.`);
  console.log(`Total found: ${result.totalFound}`);
  console.log(`New tenders inserted: ${result.totalNew}`);
  console.log(`High priority tenders: ${result.totalHighPriority}`);
  if (result.newHighPriorityTenders.length > 0) {
    console.log('\nTop High Priority Tenders:');
    for (const t of result.newHighPriorityTenders.slice(0, 3)) {
      console.log(`- [${t.clientName}] ${t.title} (${t.matchedKeywords.join(', ')})`);
    }
  }
  console.log('\n--- Test Scraping Complete ---');
}

main().catch((err) => {
  console.error('Error running scrapers:', err);
  process.exit(1);
});
