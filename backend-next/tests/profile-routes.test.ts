import { describe, it, expect, vi } from 'vitest';
import { NextRequest } from 'next/server';
import * as authHelpers from '@/lib/auth-helpers';
import { GET, PATCH } from '@/app/api/profile/route';

describe('Profile Route Handlers & BOLA/IDOR Security', () => {
  const userA = {
    id: 'user_a_id',
    email: 'userA@cyberrfp.ma',
    name: 'Analyst A',
    role: 'analyst',
    jobTitle: 'Junior Analyst',
    company: 'Alpha Corp',
    whatsappPhone: '+212600000001',
    whatsappAlertsEnabled: false,
    emailAlertsEnabled: true,
    preferredLanguage: 'fr',
    createdAt: new Date('2026-01-01T00:00:00Z'),
    updatedAt: new Date('2026-01-01T00:00:00Z'),
  };

  it('test_profile_requires_authentication', async () => {
    vi.spyOn(authHelpers, 'requireAuthenticatedUser').mockResolvedValueOnce({
      ok: false,
      response: { status: 401, json: async () => ({ error: { code: 'UNAUTHORIZED' } }) } as any,
    });

    const unauthGetReq = new NextRequest('http://localhost:3000/api/profile');
    const getRes = await GET(unauthGetReq);
    expect(getRes.status).toBe(401);

    vi.spyOn(authHelpers, 'requireAuthenticatedUser').mockResolvedValueOnce({
      ok: false,
      response: { status: 401, json: async () => ({ error: { code: 'UNAUTHORIZED' } }) } as any,
    });

    const unauthPatchReq = new NextRequest('http://localhost:3000/api/profile', {
      method: 'PATCH',
      body: JSON.stringify({ jobTitle: 'New Title' }),
    });
    const patchRes = await PATCH(unauthPatchReq);
    expect(patchRes.status).toBe(401);
  });

  it('test_get_profile_returns_only_authenticated_user (BOLA protection)', async () => {
    vi.spyOn(authHelpers, 'requireAuthenticatedUser').mockResolvedValue({
      ok: true,
      user: userA as any,
      session: { id: 'sess_1', userId: userA.id, token: 'tok_1', expiresAt: new Date() },
    });

    // Attacker sends ?userId=victim_id in query string
    const attackReq = new NextRequest('http://localhost:3000/api/profile?userId=victim_user_b');
    const res = await GET(attackReq);
    expect(res.status).toBe(200);
    const json = await res.json();
    expect(json.user.id).toBe(userA.id);
    expect(json.user.email).toBe(userA.email);
    expect(json.user.fullName).toBe('Analyst A');
  });

  it('test_patch_profile_updates_allowlisted_fields_and_e164_phone', async () => {
    let storedUser = { ...userA };
    vi.spyOn(authHelpers, 'requireAuthenticatedUser').mockResolvedValue({
      ok: true,
      user: storedUser as any,
      session: { id: 'sess_1', userId: userA.id, token: 'tok_1', expiresAt: new Date() },
    });

    // Mock DB update
    const dbModule = await import('@/db');
    const mockDb = {
      update: vi.fn().mockReturnValue({
        set: vi.fn().mockImplementation((updates) => {
          storedUser = {
            ...storedUser,
            name: updates.name ?? storedUser.name,
            jobTitle: updates.jobTitle ?? storedUser.jobTitle,
            company: updates.company ?? storedUser.company,
            whatsappPhone: updates.whatsappPhone !== undefined ? updates.whatsappPhone : storedUser.whatsappPhone,
            whatsappAlertsEnabled: updates.whatsappAlertsEnabled ?? storedUser.whatsappAlertsEnabled,
            emailAlertsEnabled: updates.emailAlertsEnabled ?? storedUser.emailAlertsEnabled,
            preferredLanguage: updates.preferredLanguage ?? storedUser.preferredLanguage,
            updatedAt: new Date(),
          };
          return {
            where: vi.fn().mockResolvedValue({ rowCount: 1 }),
          };
        }),
      }),
      select: vi.fn().mockReturnValue({
        from: vi.fn().mockReturnValue({
          where: vi.fn().mockReturnValue({
            limit: vi.fn().mockImplementation(() => Promise.resolve([storedUser])),
          }),
        }),
      }),
    };
    vi.spyOn(dbModule, 'getDb').mockReturnValue(mockDb as any);

    const patchReq = new NextRequest('http://localhost:3000/api/profile', {
      method: 'PATCH',
      body: JSON.stringify({
        fullName: 'Analyst A Updated',
        jobTitle: 'Senior Threat Hunter',
        company: 'CyberRFP Maroc',
        whatsappPhone: '+212699887766',
        whatsappAlertsEnabled: true,
        emailAlertsEnabled: false,
        preferredLanguage: 'en',
      }),
    });

    const res = await PATCH(patchReq);
    expect(res.status).toBe(200);
    const json = await res.json();
    expect(json.user.fullName).toBe('Analyst A Updated');
    expect(json.user.jobTitle).toBe('Senior Threat Hunter');
    expect(json.user.whatsappPhone).toBe('+212699887766');
    expect(json.user.whatsappAlertsEnabled).toBe(true);
    expect(json.user.emailAlertsEnabled).toBe(false);
    expect(json.user.preferredLanguage).toBe('en');

    // Also verify clearing phone with null
    const clearPhoneReq = new NextRequest('http://localhost:3000/api/profile', {
      method: 'PATCH',
      body: JSON.stringify({
        whatsappPhone: null,
      }),
    });
    const clearPhoneRes = await PATCH(clearPhoneReq);
    expect(clearPhoneRes.status).toBe(200);
    const clearJson = await clearPhoneRes.json();
    expect(clearJson.user.whatsappPhone).toBeNull();
  });

  it('test_patch_profile_rejects_invalid_phone_and_privilege_escalation', async () => {
    vi.spyOn(authHelpers, 'requireAuthenticatedUser').mockResolvedValue({
      ok: true,
      user: userA as any,
      session: { id: 'sess_1', userId: userA.id, token: 'tok_1', expiresAt: new Date() },
    });

    // 1. Attempting role escalation
    const roleEscalationReq = new NextRequest('http://localhost:3000/api/profile', {
      method: 'PATCH',
      body: JSON.stringify({
        role: 'admin',
      }),
    });
    const roleRes = await PATCH(roleEscalationReq);
    expect(roleRes.status).toBe(400);
    const roleJson = await roleRes.json();
    expect(roleJson.error.code).toBe('VALIDATION_ERROR');

    // 2. Attempting to change user ID or email
    const idEscalationReq = new NextRequest('http://localhost:3000/api/profile', {
      method: 'PATCH',
      body: JSON.stringify({
        id: 'victim_user_b',
        email: 'other@example.com',
      }),
    });
    const idRes = await PATCH(idEscalationReq);
    expect(idRes.status).toBe(400);
    const idJson = await idRes.json();
    expect(idJson.error.code).toBe('VALIDATION_ERROR');

    // 3. Invalid phone number (letters, no +, wrong length)
    const badPhoneReq = new NextRequest('http://localhost:3000/api/profile', {
      method: 'PATCH',
      body: JSON.stringify({
        whatsappPhone: '0612345678',
      }),
    });
    const badPhoneRes = await PATCH(badPhoneReq);
    expect(badPhoneRes.status).toBe(400);
    const badPhoneJson = await badPhoneRes.json();
    expect(badPhoneJson.error.code).toBe('VALIDATION_ERROR');
  });
});
