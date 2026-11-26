import { NextRequest } from 'next/server';
import { eq } from 'drizzle-orm';
import { getDb } from '@/db';
import { tenders as tendersTable, sources as sourcesTable } from '@/db/schema';
import { apiSuccess, apiError } from '@/lib/http';

export const dynamic = 'force-dynamic';

export async function GET(
  _request: NextRequest,
  context: { params: Promise<{ id: string }> }
) {
  const { id } = await context.params;

  if (!id) {
    return apiError('VALIDATION_ERROR', 'Missing tender ID', 400);
  }

  const db = getDb();
  const [tender] = await db
    .select({
      id: tendersTable.id,
      dedupHash: tendersTable.dedupHash,
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
      rawMetadata: tendersTable.rawMetadata,
      createdAt: tendersTable.createdAt,
      updatedAt: tendersTable.updatedAt,
      source: {
        id: sourcesTable.id,
        slug: sourcesTable.slug,
        name: sourcesTable.name,
        baseUrl: sourcesTable.baseUrl,
      },
    })
    .from(tendersTable)
    .leftJoin(sourcesTable, eq(tendersTable.sourceId, sourcesTable.id))
    .where(eq(tendersTable.id, id))
    .limit(1);

  if (!tender) {
    return apiError('NOT_FOUND', 'Appel d\'offres non trouvé', 404);
  }

  return apiSuccess({ tender });
}
