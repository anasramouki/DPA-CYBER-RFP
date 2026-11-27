import { getDb } from '../src/db';
import { tenders as tendersTable, sources as sourcesTable } from '../src/db/schema';
import { eq, or, ilike, ne, sql } from 'drizzle-orm';
import 'dotenv/config';

async function main() {
  const db = getDb();

  console.log('--- Checking Neon PostgreSQL database ---');

  // Find PMMP source id
  const [pmmpSource] = await db
    .select()
    .from(sourcesTable)
    .where(eq(sourcesTable.slug, 'pmmp'))
    .limit(1);

  console.log('PMMP source found:', pmmpSource);

  // Delete all tenders where source is NOT pmmp or clientName contains barid
  const deleted = await db.delete(tendersTable).where(
    or(
      pmmpSource ? ne(tendersTable.sourceId, pmmpSource.id) : undefined,
      ilike(tendersTable.clientName, '%barid%'),
      ilike(tendersTable.title, '%al barid%'),
      ilike(tendersTable.title, '%barid bank%')
    )
  );

  console.log('Cleaned non-PMMP and Barid tenders from Neon.');

  // Count remaining tenders
  const remaining = await db.select({
    id: tendersTable.id,
    ref: tendersTable.externalRef,
    client: tendersTable.clientName,
    title: tendersTable.title
  }).from(tendersTable);

  console.log(`Remaining PMMP-only tenders count: ${remaining.length}`);
  for (const r of remaining) {
    console.log(`- [${r.ref}] ${r.client}: ${r.title.slice(0, 60)}...`);
  }

  process.exit(0);
}

main().catch((err) => {
  console.error('Error cleaning Neon:', err);
  process.exit(1);
});
