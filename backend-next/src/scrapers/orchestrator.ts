import { eq, sql } from 'drizzle-orm';
import { getDb } from '@/db';
import { sources as sourcesTable, tenders as tendersTable, TenderRow } from '@/db/schema';
import { IScraper, ScraperResult, ScrapedTender } from './types';
import { generateDedupHash, matchKeywords } from './utils';

import { PMMPScraper } from './pmmp';
import { AlBaridBankScraper } from './al-barid-bank';
import { OFPPTScraper } from './ofppt';
import { SORECScraper } from './sorec';
import { AtlanticREScraper } from './atlantic-re';
import { ADMScraper } from './adm';
import { LaprophanScraper } from './laprophan';

export class ScrapingOrchestrator {
  private scrapers: Map<string, IScraper> = new Map();

  constructor() {
    // Only PMMP as requested
    this.register(new PMMPScraper());
  }

  register(scraper: IScraper) {
    this.scrapers.set(scraper.slug, scraper);
  }

  getScraper(slug: string): IScraper | undefined {
    return this.scrapers.get(slug);
  }

  listScrapers(): IScraper[] {
    return Array.from(this.scrapers.values());
  }

  async runSource(slug: string, customKeywords?: string[]): Promise<{
    result: ScraperResult;
    newTenders: TenderRow[];
    highPriorityCount: number;
  }> {
    const scraper = this.scrapers.get(slug);
    if (!scraper) {
      throw new Error(`Scraper not found for slug: ${slug}`);
    }

    const db = getDb();
    const [sourceRecord] = await db
      .select()
      .from(sourcesTable)
      .where(eq(sourcesTable.slug, slug))
      .limit(1);

    if (!sourceRecord) {
      throw new Error(`Source not found in database: ${slug}`);
    }

    const result = await scraper.scrape({ keywords: customKeywords });
    const newlyCreated: TenderRow[] = [];
    let highPriorityCount = 0;

    for (const item of result.tenders) {
      // Classify strictly by technical object/title
      const { matchedKeywords, relevanceScore, isHighPriority } = matchKeywords(
        item.title,
        customKeywords
      );

      // Skip non-cyber tenders (construction, transport, civil works, shoes, etc.)
      if (relevanceScore <= 0 || matchedKeywords.length === 0) {
        continue;
      }

      const dedupHash = generateDedupHash(
        slug,
        item.externalRef || item.directUrl,
        item.title
      );

      try {
        const inserted = await db
          .insert(tendersTable)
          .values({
            dedupHash,
            sourceId: sourceRecord.id,
            externalRef: item.externalRef,
            title: item.title,
            clientName: item.clientName,
            clientNormalized: item.clientNormalized || item.clientName.slice(0, 50),
            category: item.category || 'Non spécifié',
            publicationDate: item.publicationDate,
            deadline: item.deadline,
            directUrl: item.directUrl,
            status: item.status || 'open',
            isHighPriority,
            matchedKeywords,
            relevanceScore,
            rawMetadata: item.rawMetadata || null,
          })
          .onConflictDoNothing({ target: tendersTable.dedupHash })
          .returning();

        if (inserted.length > 0) {
          newlyCreated.push(inserted[0]);
          if (isHighPriority) {
            highPriorityCount++;
          }
        }
      } catch (insertErr: any) {
        console.error(`Error saving tender ${dedupHash}:`, insertErr.message);
      }
    }

    // Update source statistics
    await db
      .update(sourcesTable)
      .set({
        lastRunAt: sql`NOW()`,
        lastSuccessAt: sql`NOW()`,
        healthStatus: result.error ? 'error' : 'healthy',
        lastError: result.error || null,
        itemsIndexed: sql`${sourcesTable.itemsIndexed} + ${newlyCreated.length}`,
        updatedAt: sql`NOW()`,
      })
      .where(eq(sourcesTable.id, sourceRecord.id));

    return {
      result,
      newTenders: newlyCreated,
      highPriorityCount,
    };
  }

  async runAll(customKeywords?: string[]): Promise<{
    totalSources: number;
    totalFound: number;
    totalNew: number;
    totalHighPriority: number;
    newTenders: TenderRow[];
    newHighPriorityTenders: TenderRow[];
    errors: Record<string, string>;
  }> {
    const db = getDb();
    const activeSources = await db
      .select()
      .from(sourcesTable)
      .where(eq(sourcesTable.isActive, true));

    let totalFound = 0;
    let totalNew = 0;
    let totalHighPriority = 0;
    const allNewTenders: TenderRow[] = [];
    const allHighPriority: TenderRow[] = [];
    const errors: Record<string, string> = {};

    for (const src of activeSources) {
      try {
        if (!this.scrapers.has(src.slug)) {
          continue;
        }
        const outcome = await this.runSource(src.slug, customKeywords);
        totalFound += outcome.result.itemsFound;
        totalNew += outcome.newTenders.length;
        totalHighPriority += outcome.highPriorityCount;
        allNewTenders.push(...outcome.newTenders);
        allHighPriority.push(...outcome.newTenders.filter((t) => t.isHighPriority));
      } catch (err: any) {
        errors[src.slug] = err.message || 'Scraping failed';
        await db
          .update(sourcesTable)
          .set({
            lastRunAt: sql`NOW()`,
            healthStatus: 'error',
            lastError: err.message,
            updatedAt: sql`NOW()`,
          })
          .where(eq(sourcesTable.id, src.id));
      }
    }

    return {
      totalSources: activeSources.length,
      totalFound,
      totalNew,
      totalHighPriority,
      newTenders: allNewTenders,
      newHighPriorityTenders: allHighPriority,
      errors,
    };
  }
}

export const orchestrator = new ScrapingOrchestrator();
