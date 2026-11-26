import { NextRequest } from 'next/server';
import { z } from 'zod';
import { eq, and, desc } from 'drizzle-orm';
import { requireAuthenticatedUser } from '@/lib/auth-helpers';
import { getDb } from '@/db';
import { watchlist as watchlistTable } from '@/db/schema';
import { apiSuccess, apiError, parseJsonBody } from '@/lib/http';

export const dynamic = 'force-dynamic';

const addWatchlistSchema = z
  .object({
    keyword: z.string().min(2, 'Le mot-clé doit contenir au moins 2 caractères'),
    category: z.string().optional().default('cyber'),
  })
  .strict();

export async function GET(request: NextRequest) {
  const auth = await requireAuthenticatedUser(request);
  if (!auth.ok) {
    return auth.response;
  }

  const db = getDb();
  const items = await db
    .select()
    .from(watchlistTable)
    .where(eq(watchlistTable.userId, auth.user.id))
    .orderBy(desc(watchlistTable.createdAt));

  return apiSuccess({ watchlist: items });
}

export async function POST(request: NextRequest) {
  const auth = await requireAuthenticatedUser(request);
  if (!auth.ok) {
    return auth.response;
  }

  const parseResult = await parseJsonBody(request, addWatchlistSchema);
  if (!parseResult.success) {
    return parseResult.response;
  }

  const { keyword, category } = parseResult.data;
  const db = getDb();

  // Check if keyword already exists for this user
  const [existing] = await db
    .select()
    .from(watchlistTable)
    .where(
      and(
        eq(watchlistTable.userId, auth.user.id),
        eq(watchlistTable.keyword, keyword.toLowerCase().trim())
      )
    )
    .limit(1);

  if (existing) {
    return apiError('CONFLICT', 'Ce mot-clé est déjà dans votre veille', 409);
  }

  const [inserted] = await db
    .insert(watchlistTable)
    .values({
      userId: auth.user.id,
      keyword: keyword.toLowerCase().trim(),
      category: category || 'cyber',
      isActive: true,
    })
    .returning();

  return apiSuccess({ item: inserted }, 201);
}
