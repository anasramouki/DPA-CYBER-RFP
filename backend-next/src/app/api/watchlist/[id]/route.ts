import { NextRequest } from 'next/server';
import { eq, and } from 'drizzle-orm';
import { requireAuthenticatedUser } from '@/lib/auth-helpers';
import { getDb } from '@/db';
import { watchlist as watchlistTable } from '@/db/schema';
import { apiSuccess, apiError } from '@/lib/http';

export const dynamic = 'force-dynamic';

export async function DELETE(
  request: NextRequest,
  context: { params: Promise<{ id: string }> }
) {
  const auth = await requireAuthenticatedUser(request);
  if (!auth.ok) {
    return auth.response;
  }

  const { id } = await context.params;
  if (!id) {
    return apiError('VALIDATION_ERROR', 'ID manquant', 400);
  }

  const db = getDb();
  const deleted = await db
    .delete(watchlistTable)
    .where(
      and(
        eq(watchlistTable.id, id),
        eq(watchlistTable.userId, auth.user.id) // Strict BOLA scoping to current user
      )
    )
    .returning();

  if (deleted.length === 0) {
    return apiError('NOT_FOUND', 'Mot-clé introuvable ou non autorisé', 404);
  }

  return apiSuccess({ status: 'ok', deletedId: id });
}
