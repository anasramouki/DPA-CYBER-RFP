import { sql } from 'drizzle-orm';
import { sources } from './schema';
import { getDb } from './index';

export const DEFAULT_SOURCES = [
  {
    slug: 'pmmp',
    name: 'Portail Marocain des Marchés Publics (PMMP)',
    baseUrl: 'https://www.marchespublics.gov.ma',
    scraperType: 'pmmp',
    isActive: true,
    healthStatus: 'pending',
  },
  {
    slug: 'al-barid-bank',
    name: 'Al Barid Bank',
    baseUrl: 'https://fournisseurs.albaridbank.ma',
    scraperType: 'al_barid_bank',
    isActive: true,
    healthStatus: 'pending',
  },
  {
    slug: 'sorec',
    name: 'SOREC',
    baseUrl: 'https://www.sorec.ma/appels-offres/',
    scraperType: 'sorec',
    isActive: true,
    healthStatus: 'pending',
  },
  {
    slug: 'atlantic-re',
    name: 'Atlantic RE',
    baseUrl: 'https://www.atlanticre.ma',
    scraperType: 'atlantic_re',
    isActive: true,
    healthStatus: 'pending',
  },
  {
    slug: 'autoroutes-du-maroc',
    name: 'Autoroutes du Maroc (ADM)',
    baseUrl: 'https://www.adm.co.ma',
    scraperType: 'adm',
    isActive: true,
    healthStatus: 'pending',
  },
  {
    slug: 'laprophan',
    name: 'Laprophan',
    baseUrl: 'https://www.laprophan.com',
    scraperType: 'laprophan',
    isActive: true,
    healthStatus: 'pending',
  },
  {
    slug: 'ofppt',
    name: 'OFPPT',
    baseUrl: 'https://www.ofppt.ma',
    scraperType: 'ofppt',
    isActive: true,
    healthStatus: 'pending',
  },
];

export async function seedSources(db: any): Promise<number> {
  let count = 0;
  for (const src of DEFAULT_SOURCES) {
    await db
      .insert(sources)
      .values(src)
      .onConflictDoUpdate({
        target: sources.slug,
        set: {
          name: sql`EXCLUDED.name`,
          baseUrl: sql`EXCLUDED.base_url`,
          scraperType: sql`EXCLUDED.scraper_type`,
          updatedAt: sql`NOW()`,
        },
      });
    count++;
  }
  return count;
}

// CLI execution guard
if (
  typeof process !== 'undefined' &&
  process.argv &&
  process.argv[1] &&
  (process.argv[1].endsWith('seed.ts') || process.argv[1].endsWith('seed.js'))
) {
  (async () => {
    try {
      const db = getDb();
      console.log('Seeding Moroccan procurement sources into database...');
      const seeded = await seedSources(db);
      console.log(`Successfully seeded ${seeded} sources into database.`);
      process.exit(0);
    } catch (error) {
      console.error('Failed to seed sources:', error);
      process.exit(1);
    }
  })();
}
