import { NextRequest } from 'next/server';
import { orchestrator } from '@/scrapers/orchestrator';
import { dispatchHighPriorityAlerts } from '@/lib/alerts/whatsapp';
import { apiSuccess, apiError } from '@/lib/http';

export const dynamic = 'force-dynamic';
export const maxDuration = 60; // Fluid compute max execution for scrapers

export async function GET(request: NextRequest) {
  return handleCronScrape(request);
}

export async function POST(request: NextRequest) {
  return handleCronScrape(request);
}

async function handleCronScrape(request: NextRequest) {
  const cronSecret = process.env.CRON_SECRET;
  const authHeader = request.headers.get('authorization');

  // Verify CRON_SECRET if configured in production
  if (cronSecret && process.env.NODE_ENV === 'production') {
    if (authHeader !== `Bearer ${cronSecret}`) {
      return apiError('UNAUTHORIZED', 'Unauthorized cron invocation', 401);
    }
  }

  try {
    const startTime = Date.now();
    const scrapeSummary = await orchestrator.runAll();

    // Trigger WhatsApp notifications for newly detected High Priority tenders
    let alertsSent = 0;
    if (scrapeSummary.newHighPriorityTenders.length > 0) {
      const alertResults = await dispatchHighPriorityAlerts(scrapeSummary.newHighPriorityTenders);
      alertsSent = alertResults.filter((r) => r.success).length;
    }

    return apiSuccess({
      status: 'ok',
      durationMs: Date.now() - startTime,
      totalSources: scrapeSummary.totalSources,
      totalFound: scrapeSummary.totalFound,
      totalNewTenders: scrapeSummary.totalNew,
      totalHighPriority: scrapeSummary.totalHighPriority,
      newTenders: scrapeSummary.newTenders.map((t) => ({
        id: t.id,
        title: t.title,
        client: t.clientName,
        isHighPriority: t.isHighPriority,
        matchedKeywords: t.matchedKeywords,
      })),
      alertsSent,
      errors: scrapeSummary.errors,
    });
  } catch (err: any) {
    return apiError('INTERNAL_ERROR', err.message || 'Scraping automation failed', 500);
  }
}
