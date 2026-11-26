import { NextRequest, NextResponse } from 'next/server';
import { eq } from 'drizzle-orm';
import { getDb } from '@/db';
import { tenders as tendersTable } from '@/db/schema';
import { apiError } from '@/lib/http';

export const dynamic = 'force-dynamic';

export async function GET(
  _request: NextRequest,
  { params }: { params: Promise<{ id: string }> }
) {
  const { id } = await params;
  const db = getDb();

  const [tender] = await db
    .select({
      id: tendersTable.id,
      directUrl: tendersTable.directUrl,
      rawMetadata: tendersTable.rawMetadata,
    })
    .from(tendersTable)
    .where(eq(tendersTable.id, id))
    .limit(1);

  if (!tender) {
    return apiError('NOT_FOUND', 'Tender not found', 404);
  }

  let dceUrl = (tender.rawMetadata as any)?.dceUrl;

  if (!dceUrl && tender.directUrl) {
    const refMatch = tender.directUrl.match(/refConsultation=([0-9]+)/);
    const orgMatch = tender.directUrl.match(/orgAcronyme=([A-Za-z0-9_\-]+)/);
    if (refMatch && orgMatch) {
      dceUrl = `https://www.marchespublics.gov.ma/index.php?page=entreprise.EntrepriseDemandeTelechargementDce&refConsultation=${refMatch[1]}&orgAcronyme=${orgMatch[2]}`;
    } else {
      dceUrl = tender.directUrl;
    }
  }

  const destination = dceUrl || tender.directUrl || 'https://www.marchespublics.gov.ma';
  return NextResponse.redirect(destination, { status: 307 });
}
