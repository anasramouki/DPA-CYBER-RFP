import { NextRequest } from 'next/server';
import { ilike, or, eq, desc, and, sql, count, gt } from 'drizzle-orm';
import { getDb } from '@/db';
import { tenders as tendersTable, sources as sourcesTable } from '@/db/schema';
import { apiSuccess } from '@/lib/http';

export const dynamic = 'force-dynamic';

export async function GET(request: NextRequest) {
  const searchParams = request.nextUrl.searchParams;
  const search = searchParams.get('search')?.trim();
  const status = searchParams.get('status')?.trim();
  const sourceSlug = searchParams.get('source')?.trim();
  const priority = searchParams.get('priority')?.trim();
  const page = Math.max(1, parseInt(searchParams.get('page') || '1', 10));
  const limit = Math.min(100, Math.max(1, parseInt(searchParams.get('limit') || '20', 10)));
  const offset = (page - 1) * limit;

  const db = getDb();

  const conditions = [];

  // Strictly require positive cyber relevance (reject construction, transport, civil works, etc.)
  conditions.push(gt(tendersTable.relevanceScore, 0));

  if (search) {
    conditions.push(
      or(
        ilike(tendersTable.title, `%${search}%`),
        ilike(tendersTable.clientName, `%${search}%`),
        ilike(tendersTable.externalRef, `%${search}%`)
      )
    );
  }

  if (status) {
    conditions.push(eq(tendersTable.status, status));
  }

  if (priority === 'high') {
    conditions.push(eq(tendersTable.isHighPriority, true));
  }

  // Strictly filter to PMMP source only (ignoring press and third-party sources)
  const [matchedSource] = await db
    .select({ id: sourcesTable.id })
    .from(sourcesTable)
    .where(eq(sourcesTable.slug, 'pmmp'))
    .limit(1);

  if (matchedSource) {
    conditions.push(eq(tendersTable.sourceId, matchedSource.id));
  }

  const whereClause = conditions.length > 0 ? and(...conditions) : undefined;

  // Get total count
  const [{ totalCount }] = await db
    .select({ totalCount: count() })
    .from(tendersTable)
    .where(whereClause);

  // Get paginated items with source info
  const items = await db
    .select({
      id: tendersTable.id,
      externalRef: tendersTable.externalRef,
      title: tendersTable.title,
      clientName: tendersTable.clientName,
      clientNormalized: tendersTable.clientNormalized,
      category: tendersTable.category,
      publicationDate: tendersTable.publicationDate,
      deadline: tendersTable.deadline,
      directUrl: tendersTable.directUrl,
      status: tendersTable.status,
      isHighPriority: tendersTable.isHighPriority,
      matchedKeywords: tendersTable.matchedKeywords,
      relevanceScore: tendersTable.relevanceScore,
      createdAt: tendersTable.createdAt,
      sourceSlug: sourcesTable.slug,
      sourceName: sourcesTable.name,
    })
    .from(tendersTable)
    .leftJoin(sourcesTable, eq(tendersTable.sourceId, sourcesTable.id))
    .where(whereClause)
    .orderBy(desc(tendersTable.createdAt))
    .limit(limit)
    .offset(offset);

  const total = Number(totalCount);
  const totalPages = Math.ceil(total / limit);

  return apiSuccess({
    items,
    pagination: {
      total,
      page,
      limit,
      totalPages,
    },
  });
}
