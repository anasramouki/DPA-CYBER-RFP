import { NextRequest } from 'next/server';
import { requireAuthenticatedUser } from '@/lib/auth-helpers';
import { sendWhatsAppMessage, formatWhatsAppMessage } from '@/lib/alerts/whatsapp';
import { apiSuccess, apiError } from '@/lib/http';

export const dynamic = 'force-dynamic';

export async function POST(request: NextRequest) {
  const auth = await requireAuthenticatedUser(request);
  if (!auth.ok) {
    return auth.response;
  }

  const phone = auth.user.whatsappPhone;
  if (!phone) {
    return apiError(
      'VALIDATION_ERROR',
      'Aucun numéro WhatsApp configuré sur votre profil. Mettez à jour votre profil avec votre numéro au format E.164 (ex: +212612345678).',
      400
    );
  }

  const sampleTender = {
    clientName: 'Direction Générale de la Sécurité des Systèmes d\'Information (DGSSI)',
    title: 'Test CyberRFP - Audit et Surveillance SOC 24/7',
    deadline: new Date(Date.now() + 15 * 86400000),
    directUrl: 'https://www.marchespublics.gov.ma',
  };

  const message = formatWhatsAppMessage(sampleTender);
  const result = await sendWhatsAppMessage(phone, message);

  if (!result.success) {
    return apiError('INTERNAL_ERROR', result.error || 'Échec de l\'envoi WhatsApp', 500);
  }

  return apiSuccess({
    status: 'ok',
    message: 'Alerte WhatsApp test envoyée avec succès',
    recipient: phone,
    messageId: result.messageId,
  });
}
