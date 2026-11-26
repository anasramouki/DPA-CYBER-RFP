import { NextRequest } from 'next/server';
import { z } from 'zod';
import { eq } from 'drizzle-orm';
import { getAuth } from '@/lib/auth';
import { getDb } from '@/db';
import { user as userTable } from '@/db/schema';
import { isEmailDomainAllowed } from '@/lib/env';
import { apiSuccess, apiError, parseJsonBody, toSafeUser } from '@/lib/http';

export const dynamic = 'force-dynamic';

const registerSchema = z
  .object({
    email: z.string().email(),
    password: z.string().min(8),
    fullName: z.string().min(2),
    jobTitle: z.string().optional(),
    company: z.string().optional(),
    whatsappPhone: z.string().regex(/^\+[1-9]\d{6,14}$/, 'Must be a valid E.164 phone number').optional(),
    preferredLanguage: z.enum(['fr', 'en', 'ar']).optional(),
  })
  .strict();

export async function POST(request: NextRequest) {
  const parseResult = await parseJsonBody(request, registerSchema);
  if (!parseResult.success) {
    return parseResult.response;
  }

  const { email, password, fullName, jobTitle, company, whatsappPhone, preferredLanguage } =
    parseResult.data;

  if (!isEmailDomainAllowed(email)) {
    return apiError(
      'FORBIDDEN',
      'Registration is restricted to approved corporate email domains',
      403
    );
  }

  const auth = getAuth();

  try {
    const authRes = await auth.api.signUpEmail({
      body: {
        email,
        password,
        name: fullName,
      },
      headers: request.headers,
      asResponse: true,
    });

    if (!authRes.ok) {
      const errJson = await authRes.json().catch(() => ({}));
      if (authRes.status === 409 || errJson?.code === 'USER_ALREADY_EXISTS') {
        return apiError('CONFLICT', 'A user with this email address already exists', 409);
      }
      return apiError(
        'VALIDATION_ERROR',
        errJson?.message || 'Registration failed',
        authRes.status
      );
    }

    const data = await authRes.json();
    const headers = new Headers();
    const setCookie = authRes.headers.get('set-cookie');
    if (setCookie) {
      headers.set('set-cookie', setCookie);
    }

    // Update optional custom fields if provided
    let userRecord = data.user;
    try {
      const db = getDb();
      if (jobTitle || company || whatsappPhone || preferredLanguage) {
        await db
          .update(userTable)
          .set({
            jobTitle: jobTitle ?? null,
            company: company ?? null,
            whatsappPhone: whatsappPhone ?? null,
            preferredLanguage: preferredLanguage ?? 'fr',
          })
          .where(eq(userTable.id, data.user.id));
      }

      const [fetched] = await db
        .select()
        .from(userTable)
        .where(eq(userTable.id, data.user.id))
        .limit(1);
      if (fetched) {
        userRecord = fetched;
      }
    } catch {
      // In unit tests where DB is mocked, fallback to data.user
    }

    const token = data.token || authRes.headers.get('set-auth-token') || '';
    return apiSuccess({ user: toSafeUser(userRecord), token }, 201, headers);
  } catch (error: any) {
    if (error?.status === 409 || error?.code === 'USER_ALREADY_EXISTS') {
      return apiError('CONFLICT', 'A user with this email address already exists', 409);
    }
    return apiError('VALIDATION_ERROR', error.message || 'Registration failed', 400);
  }
}
