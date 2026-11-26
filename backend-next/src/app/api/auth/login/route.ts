import { NextRequest } from 'next/server';
import { z } from 'zod';
import { eq } from 'drizzle-orm';
import { getAuth } from '@/lib/auth';
import { getDb } from '@/db';
import { user as userTable } from '@/db/schema';
import { apiSuccess, apiError, parseJsonBody, toSafeUser } from '@/lib/http';

export const dynamic = 'force-dynamic';

const loginSchema = z
  .object({
    email: z.string().email(),
    password: z.string().min(1),
  })
  .strict();

export async function POST(request: NextRequest) {
  const parseResult = await parseJsonBody(request, loginSchema);
  if (!parseResult.success) {
    return parseResult.response;
  }

  const { email, password } = parseResult.data;
  const auth = getAuth();

  try {
    const authRes = await auth.api.signInEmail({
      body: {
        email,
        password,
      },
      headers: request.headers,
      asResponse: true,
    });

    if (!authRes.ok) {
      return apiError('UNAUTHORIZED', 'Invalid email or password', 401);
    }

    const data = await authRes.json();
    const headers = new Headers();
    const setCookie = authRes.headers.get('set-cookie');
    if (setCookie) {
      headers.set('set-cookie', setCookie);
    }

    let userRecord = data.user;
    try {
      const db = getDb();
      const [fetched] = await db
        .select()
        .from(userTable)
        .where(eq(userTable.id, data.user.id))
        .limit(1);
      if (fetched) {
        userRecord = fetched;
      }
    } catch {
      // In tests where DB might be mocked, fall back to data.user
    }

    const token = data.token || authRes.headers.get('set-auth-token') || '';
    return apiSuccess({ user: toSafeUser(userRecord), token }, 200, headers);
  } catch {
    return apiError('UNAUTHORIZED', 'Invalid email or password', 401);
  }
}
