import { NextRequest } from 'next/server';
import { desc } from 'drizzle-orm';
import { getDb } from '@/db';
import { sources as sourcesTable } from '@/db/schema';
import { apiSuccess } from '@/lib/http';

export const dynamic = 'force-dynamic';

export async function GET() {
  const db = getDb();
  const sourcesList = await db
    .select({
      id: sourcesTable.id,
      slug: sourcesTable.slug,
      name: sourcesTable.name,
      baseUrl: sourcesTable.baseUrl,
      scraperType: sourcesTable.scraperType,
      isActive: sourcesTable.isActive,
      healthStatus: sourcesTable.healthStatus,
      lastRunAt: sourcesTable.lastRunAt,
      lastSuccessAt: sourcesTable.lastSuccessAt,
      lastError: sourcesTable.lastError,
      itemsIndexed: sourcesTable.itemsIndexed,
      updatedAt: sourcesTable.updatedAt,
    })
    .from(sourcesTable)
    .orderBy(desc(sourcesTable.itemsIndexed));

  return apiSuccess({
    sources: sourcesList,
    total: sourcesList.length,
    active: sourcesList.filter((s) => s.isActive).length,
  });
}
