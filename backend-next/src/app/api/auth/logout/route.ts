import { NextRequest } from 'next/server';
import { getAuth } from '@/lib/auth';
import { apiSuccess } from '@/lib/http';

export const dynamic = 'force-dynamic';

export async function POST(request: NextRequest) {
  const auth = getAuth();
  const headers = new Headers();

  try {
    const authRes = await auth.api.signOut({
      headers: request.headers,
      asResponse: true,
    });

    const setCookie = authRes?.headers?.get('set-cookie');
    if (setCookie) {
      headers.set('set-cookie', setCookie);
    }
  } catch {
    // Session is signed out regardless
  }

  return apiSuccess({ status: 'ok' }, 200, headers);
}
