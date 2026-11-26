import { apiSuccess, apiError } from '@/lib/http';
import { checkDatabaseHealth } from '@/db';

export const dynamic = 'force-dynamic';

export async function GET() {
  const isHealthy = await checkDatabaseHealth();
  if (!isHealthy) {
    return apiError('INTERNAL_ERROR', 'Database connection failed', 503);
  }

  return apiSuccess({
    status: 'ok',
    database: 'connected',
    timestamp: new Date().toISOString(),
  });
}
