import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';
import { NextRequest } from 'next/server';

describe('Auth Route Handlers', () => {
  const originalEnv = { ...process.env };

  beforeEach(() => {
    process.env = { ...originalEnv };
  });

  afterEach(() => {
    process.env = originalEnv;
  });

  it('test_register_validates_payload_and_rejects_role_escalation', async () => {
    const { POST: registerHandler } = await import('@/app/api/auth/register/route');

    // 1. Attempting role escalation via body
    const roleEscalationReq = new NextRequest('http://localhost:3000/api/auth/register', {
      method: 'POST',
      body: JSON.stringify({
        email: 'attacker@example.com',
        password: 'password123',
        fullName: 'Attacker User',
        role: 'admin', // Should be rejected by strict schema
      }),
    });
    const roleEscalationRes = await registerHandler(roleEscalationReq);
    expect(roleEscalationRes.status).toBe(400);
    const roleEscalationJson = await roleEscalationRes.json();
    expect(roleEscalationJson.error.code).toBe('VALIDATION_ERROR');

    // 2. Short password (< 8 chars)
    const shortPwReq = new NextRequest('http://localhost:3000/api/auth/register', {
      method: 'POST',
      body: JSON.stringify({
        email: 'user@example.com',
        password: '123',
        fullName: 'Valid Name',
      }),
    });
    const shortPwRes = await registerHandler(shortPwReq);
    expect(shortPwRes.status).toBe(400);
    const shortPwJson = await shortPwRes.json();
    expect(shortPwJson.error.code).toBe('VALIDATION_ERROR');

    // 3. Invalid phone format (not E.164)
    const badPhoneReq = new NextRequest('http://localhost:3000/api/auth/register', {
      method: 'POST',
      body: JSON.stringify({
        email: 'user@example.com',
        password: 'password123',
        fullName: 'Valid Name',
        whatsappPhone: '0612345678', // Missing +
      }),
    });
    const badPhoneRes = await registerHandler(badPhoneReq);
    expect(badPhoneRes.status).toBe(400);
    const badPhoneJson = await badPhoneRes.json();
    expect(badPhoneJson.error.code).toBe('VALIDATION_ERROR');
  });

  it('test_register_enforces_allowed_email_domains_when_configured', async () => {
    process.env.ALLOWED_EMAIL_DOMAINS = 'dpg-cyber.com,example.ma';
    const { POST: registerHandler } = await import('@/app/api/auth/register/route');

    const blockedReq = new NextRequest('http://localhost:3000/api/auth/register', {
      method: 'POST',
      body: JSON.stringify({
        email: 'user@gmail.com',
        password: 'password123',
        fullName: 'Public Gmail User',
      }),
    });
    const blockedRes = await registerHandler(blockedReq);
    expect(blockedRes.status).toBe(403);
    const blockedJson = await blockedRes.json();
    expect(blockedJson.error.code).toBe('FORBIDDEN');
    expect(blockedJson.error.message).toMatch(/domain/i);
  });

  it('test_register_creates_user_with_analyst_role_and_returns_token_and_cookie', async () => {
    delete process.env.ALLOWED_EMAIL_DOMAINS;
    const authModule = await import('@/lib/auth');
    const { POST: registerHandler } = await import('@/app/api/auth/register/route');

    const mockUser = {
      id: 'usr_new_1',
      email: 'analyst@cyberrfp.ma',
      name: 'Amine Bennani',
      role: 'analyst',
      jobTitle: 'SOC Lead',
      company: 'CyberRFP',
      whatsappPhone: '+212611223344',
      whatsappAlertsEnabled: false,
      emailAlertsEnabled: true,
      preferredLanguage: 'fr',
      createdAt: new Date('2026-02-01T10:00:00Z'),
      updatedAt: new Date('2026-02-01T10:00:00Z'),
    };

    const mockResponseHeaders = new Headers();
    mockResponseHeaders.set('set-cookie', 'better-auth.session_token=token123; Path=/; HttpOnly');
    mockResponseHeaders.set('set-auth-token', 'token123');

    const mockAuth = {
      api: {
        signUpEmail: vi.fn().mockResolvedValue({
          ok: true,
          status: 200,
          headers: mockResponseHeaders,
          json: async () => ({
            token: 'token123',
            user: mockUser,
          }),
        }),
      },
    };

    const authSpy = vi.spyOn(authModule, 'getAuth').mockReturnValue(mockAuth as any);

    const req = new NextRequest('http://localhost:3000/api/auth/register', {
      method: 'POST',
      body: JSON.stringify({
        email: 'analyst@cyberrfp.ma',
        password: 'SecurePassword123!',
        fullName: 'Amine Bennani',
        jobTitle: 'SOC Lead',
        company: 'CyberRFP',
        whatsappPhone: '+212611223344',
        preferredLanguage: 'fr',
      }),
    });

    const res = await registerHandler(req);
    expect(res.status).toBe(201);
    const json = await res.json();
    expect(json.token).toBe('token123');
    expect(json.user.role).toBe('analyst');
    expect(json.user.fullName).toBe('Amine Bennani');
    expect(json.user.id).toBe('usr_new_1');
    expect(res.headers.get('set-cookie')).toContain('better-auth.session_token');

    authSpy.mockRestore();
  });

  it('test_login_returns_safe_user_and_bearer_token_or_401_on_bad_credentials', async () => {
    const authModule = await import('@/lib/auth');
    const { POST: loginHandler } = await import('@/app/api/auth/login/route');

    const mockUser = {
      id: 'usr_existing_1',
      email: 'analyst@cyberrfp.ma',
      name: 'Amine Bennani',
      role: 'analyst',
      jobTitle: 'SOC Lead',
      company: 'CyberRFP',
      whatsappPhone: '+212611223344',
      whatsappAlertsEnabled: false,
      emailAlertsEnabled: true,
      preferredLanguage: 'fr',
      createdAt: new Date('2026-02-01T10:00:00Z'),
      updatedAt: new Date('2026-02-01T10:00:00Z'),
    };

    const mockResponseHeaders = new Headers();
    mockResponseHeaders.set('set-cookie', 'better-auth.session_token=token_login_abc; Path=/; HttpOnly');

    // 1. Valid credentials
    const mockAuthSuccess = {
      api: {
        signInEmail: vi.fn().mockResolvedValue({
          ok: true,
          status: 200,
          headers: mockResponseHeaders,
          json: async () => ({
            token: 'token_login_abc',
            user: mockUser,
          }),
        }),
      },
    };

    const authSpy = vi.spyOn(authModule, 'getAuth').mockReturnValue(mockAuthSuccess as any);

    const validReq = new NextRequest('http://localhost:3000/api/auth/login', {
      method: 'POST',
      body: JSON.stringify({
        email: 'analyst@cyberrfp.ma',
        password: 'ValidPassword123!',
      }),
    });
    const validRes = await loginHandler(validReq);
    expect(validRes.status).toBe(200);
    const validJson = await validRes.json();
    expect(validJson.token).toBe('token_login_abc');
    expect(validJson.user.email).toBe('analyst@cyberrfp.ma');
    expect(validRes.headers.get('set-cookie')).toContain('better-auth.session_token');

    // 2. Invalid credentials
    mockAuthSuccess.api.signInEmail.mockResolvedValueOnce({
      ok: false,
      status: 401,
      headers: new Headers(),
      json: async () => ({ code: 'INVALID_EMAIL_OR_PASSWORD', message: 'Invalid email or password' }),
    });

    const badReq = new NextRequest('http://localhost:3000/api/auth/login', {
      method: 'POST',
      body: JSON.stringify({
        email: 'analyst@cyberrfp.ma',
        password: 'WrongPassword!',
      }),
    });
    const badRes = await loginHandler(badReq);
    expect(badRes.status).toBe(401);
    const badJson = await badRes.json();
    expect(badJson.error.code).toBe('UNAUTHORIZED');

    authSpy.mockRestore();
  });

  it('test_logout_revokes_session_and_clears_cookie', async () => {
    const authModule = await import('@/lib/auth');
    const { POST: logoutHandler } = await import('@/app/api/auth/logout/route');

    const clearHeaders = new Headers();
    clearHeaders.set('set-cookie', 'better-auth.session_token=; Path=/; Max-Age=0');

    const mockAuth = {
      api: {
        signOut: vi.fn().mockResolvedValue({
          ok: true,
          status: 200,
          headers: clearHeaders,
        }),
      },
    };

    const authSpy = vi.spyOn(authModule, 'getAuth').mockReturnValue(mockAuth as any);

    const req = new NextRequest('http://localhost:3000/api/auth/logout', {
      method: 'POST',
      headers: {
        authorization: 'Bearer token_to_revoke',
      },
    });

    const res = await logoutHandler(req);
    expect(res.status).toBe(200);
    const json = await res.json();
    expect(json.status).toBe('ok');
    expect(res.headers.get('set-cookie')).toContain('Max-Age=0');

    authSpy.mockRestore();
  });
});
