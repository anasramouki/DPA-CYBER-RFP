import 'dotenv/config';
import { eq, or, sql, notInArray } from 'drizzle-orm';
import { getDb } from './index';
import { tenders as tendersTable } from './schema';
import { matchKeywords, EXCLUDED_NON_CYBER_KEYWORDS } from '../scrapers/utils';

async function cleanupTenders() {
  console.log('Cleaning up non-cyber tenders from database...');
  const db = getDb();

  const allTenders = await db.select().from(tendersTable);
  console.log(`Found ${allTenders.length} total tenders in DB.`);

  let deleted = 0;
  let updated = 0;

  for (const t of allTenders) {
    const { matchedKeywords, relevanceScore, isHighPriority } = matchKeywords(t.title);

    if (relevanceScore <= 0 || matchedKeywords.length === 0) {
      console.log(`❌ Deleting non-cyber: [${t.externalRef}] ${t.title}`);
      await db.delete(tendersTable).where(eq(tendersTable.id, t.id));
      deleted++;
    } else {
      console.log(`✓ Keeping cyber tender: [${t.externalRef}] ${t.title} -> ${matchedKeywords.join(', ')}`);
      await db
        .update(tendersTable)
        .set({
          matchedKeywords,
          relevanceScore,
          isHighPriority,
        })
        .where(eq(tendersTable.id, t.id));
      updated++;
    }
  }

  console.log(`Done! Deleted: ${deleted}, Retained & Updated: ${updated}`);
}

cleanupTenders()
  .then(() => process.exit(0))
  .catch((err) => {
    console.error('Cleanup error:', err);
    process.exit(1);
  });
