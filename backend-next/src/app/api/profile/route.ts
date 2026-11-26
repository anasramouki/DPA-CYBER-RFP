import { NextRequest } from 'next/server';
import { z } from 'zod';
import { eq, sql } from 'drizzle-orm';
import { requireAuthenticatedUser } from '@/lib/auth-helpers';
import { getDb } from '@/db';
import { user as userTable } from '@/db/schema';
import { apiSuccess, apiError, parseJsonBody, toSafeUser } from '@/lib/http';

export const dynamic = 'force-dynamic';

const patchProfileSchema = z
  .object({
    fullName: z.string().min(2).optional(),
    jobTitle: z.string().nullable().optional(),
    company: z.string().nullable().optional(),
    whatsappPhone: z
      .string()
      .regex(/^\+[1-9]\d{6,14}$/, 'Must be a valid E.164 phone number')
      .nullable()
      .optional(),
    whatsappAlertsEnabled: z.boolean().optional(),
    emailAlertsEnabled: z.boolean().optional(),
    preferredLanguage: z.enum(['fr', 'en', 'ar']).optional(),
  })
  .strict();

export async function GET(request: NextRequest) {
  const authResult = await requireAuthenticatedUser(request);
  if (!authResult.ok) {
    return authResult.response;
  }

  return apiSuccess({ user: toSafeUser(authResult.user) });
}

export async function PATCH(request: NextRequest) {
  const authResult = await requireAuthenticatedUser(request);
  if (!authResult.ok) {
    return authResult.response;
  }

  const parseResult = await parseJsonBody(request, patchProfileSchema);
  if (!parseResult.success) {
    return parseResult.response;
  }

  const updates = parseResult.data;
  const dbUpdates: Record<string, any> = {
    updatedAt: sql`NOW()`,
  };

  if (updates.fullName !== undefined) {
    dbUpdates.name = updates.fullName;
  }
  if (updates.jobTitle !== undefined) {
    dbUpdates.jobTitle = updates.jobTitle;
  }
  if (updates.company !== undefined) {
    dbUpdates.company = updates.company;
  }
  if (updates.whatsappPhone !== undefined) {
    dbUpdates.whatsappPhone = updates.whatsappPhone;
  }
  if (updates.whatsappAlertsEnabled !== undefined) {
    dbUpdates.whatsappAlertsEnabled = updates.whatsappAlertsEnabled;
  }
  if (updates.emailAlertsEnabled !== undefined) {
    dbUpdates.emailAlertsEnabled = updates.emailAlertsEnabled;
  }
  if (updates.preferredLanguage !== undefined) {
    dbUpdates.preferredLanguage = updates.preferredLanguage;
  }

  const db = getDb();
  await db
    .update(userTable)
    .set(dbUpdates)
    .where(eq(userTable.id, authResult.user.id));

  const [updatedUser] = await db
    .select()
    .from(userTable)
    .where(eq(userTable.id, authResult.user.id))
    .limit(1);

  return apiSuccess({ user: toSafeUser(updatedUser || authResult.user) });
}
