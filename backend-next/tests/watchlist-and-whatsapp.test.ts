import { describe, it, expect, vi } from 'vitest';
import { NextRequest } from 'next/server';
import { formatWhatsAppMessage, sendWhatsAppMessage } from '@/lib/alerts/whatsapp';
import * as authHelpers from '@/lib/auth-helpers';
import { GET as getWatchlist, POST as postWatchlist } from '@/app/api/watchlist/route';

describe('Milestone 4: WhatsApp Alerts & Watchlist Tests', () => {
  it('test_format_whatsapp_message_matches_exact_specification', () => {
    const tender = {
      clientName: 'Al Barid Bank',
      title: 'Fourniture de pare-feu et licences DLP Forcepoint',
      deadline: new Date('2026-12-15T12:00:00Z'),
      directUrl: 'https://fournisseurs.albaridbank.ma/detail/123',
    };

    const formatted = formatWhatsAppMessage(tender);
    expect(formatted).toContain('🚨 *Nouvel Appel d\'Offre* 🚨');
    expect(formatted).toContain('*Client:* Al Barid Bank');
    expect(formatted).toContain('*Titre:* Fourniture de pare-feu et licences DLP Forcepoint');
    expect(formatted).toContain('*Deadline:* 15/12/2026');
    expect(formatted).toContain('*Lien:* https://fournisseurs.albaridbank.ma/detail/123');
  });

  it('test_send_whatsapp_message_simulator_mode', async () => {
    const res = await sendWhatsAppMessage('+212612345678', 'Test message');
    expect(res.success).toBe(true);
    expect(res.messageId).toBeTruthy();
  });

  it('test_watchlist_requires_auth_and_rejects_unauthenticated', async () => {
    vi.spyOn(authHelpers, 'requireAuthenticatedUser').mockResolvedValueOnce({
      ok: false,
      response: { status: 401, json: async () => ({ error: { code: 'UNAUTHORIZED' } }) } as any,
    });

    const req = new NextRequest('http://localhost:3000/api/watchlist');
    const res = await getWatchlist(req);
    expect(res.status).toBe(401);
  });
});
