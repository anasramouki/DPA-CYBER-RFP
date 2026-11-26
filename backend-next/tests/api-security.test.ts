import { describe, it, expect, vi } from 'vitest';
import { NextRequest } from 'next/server';
import * as authHelpers from '@/lib/auth-helpers';
import { GET as getProfile, PATCH as patchProfile } from '@/app/api/profile/route';
import { GET as getWatchlist, POST as postWatchlist } from '@/app/api/watchlist/route';
import { DELETE as deleteWatchlist } from '@/app/api/watchlist/[id]/route';

describe('Milestone 5: API Security & BOLA / IDOR Audit', () => {
  const victimUser = {
    id: 'usr_victim_456',
    email: 'victim@cyberrfp.ma',
    name: 'Victim User',
    role: 'analyst',
    jobTitle: 'CISO',
    company: 'Victim Corp',
    whatsappPhone: '+212611111111',
    whatsappAlertsEnabled: true,
    emailAlertsEnabled: true,
    preferredLanguage: 'fr',
    createdAt: new Date(),
    updatedAt: new Date(),
  };

  const attackerUser = {
    id: 'usr_attacker_789',
    email: 'attacker@cyberrfp.ma',
    name: 'Attacker User',
    role: 'analyst',
    jobTitle: 'Hacker',
    company: 'Evil Corp',
    whatsappPhone: '+212699999999',
    whatsappAlertsEnabled: false,
    emailAlertsEnabled: false,
    preferredLanguage: 'fr',
    createdAt: new Date(),
    updatedAt: new Date(),
  };

  it('BOLA Audit: Attacker cannot access or modify victim profile', async () => {
    // Authenticated as attacker
    vi.spyOn(authHelpers, 'requireAuthenticatedUser').mockResolvedValue({
      ok: true,
      user: attackerUser as any,
      session: { id: 'sess_att', userId: attackerUser.id, token: 'tok_att', expiresAt: new Date() },
    });

    // Attacker tries to read victim's profile via spoofed query params
    const getReq = new NextRequest(`http://localhost:3000/api/profile?userId=${victimUser.id}`);
    const getRes = await getProfile(getReq);
    expect(getRes.status).toBe(200);
    const getJson = await getRes.json();
    expect(getJson.user.id).toBe(attackerUser.id);
    expect(getJson.user.email).toBe(attackerUser.email);
    expect(getJson.user.id).not.toBe(victimUser.id);

    // Attacker tries privilege escalation via PATCH
    const patchReq = new NextRequest('http://localhost:3000/api/profile', {
      method: 'PATCH',
      body: JSON.stringify({
        role: 'admin',
        id: victimUser.id,
      }),
    });
    const patchRes = await patchProfile(patchReq);
    expect(patchRes.status).toBe(400);
    const patchJson = await patchRes.json();
    expect(patchJson.error.code).toBe('VALIDATION_ERROR');
  });

  it('BOLA Audit: Attacker cannot delete victim watchlist item', async () => {
    // Authenticated as attacker
    vi.spyOn(authHelpers, 'requireAuthenticatedUser').mockResolvedValue({
      ok: true,
      user: attackerUser as any,
      session: { id: 'sess_att', userId: attackerUser.id, token: 'tok_att', expiresAt: new Date() },
    });

    // Mock DB delete returning empty because userId does not match
    const dbModule = await import('@/db');
    vi.spyOn(dbModule, 'getDb').mockReturnValue({
      delete: vi.fn().mockReturnValue({
        where: vi.fn().mockReturnValue({
          returning: vi.fn().mockResolvedValue([]), // 0 rows deleted because of userId check
        }),
      }),
    } as any);

    const deleteReq = new NextRequest('http://localhost:3000/api/watchlist/item_belonging_to_victim', {
      method: 'DELETE',
    });
    const deleteRes = await deleteWatchlist(deleteReq, {
      params: Promise.resolve({ id: 'item_belonging_to_victim' }),
    });

    // Must return 404 when item doesn't belong to current user
    expect(deleteRes.status).toBe(404);
  });
});
