import { describe, it, expect, beforeEach, afterEach } from 'vitest';
import { NextRequest } from 'next/server';
import { isEmailDomainAllowed } from '@/lib/env';
import { apiError, toSafeUser } from '@/lib/http';
import { proxy } from '@/proxy';

describe('HTTP & Env Helpers', () => {
  const originalEnv = { ...process.env };

  beforeEach(() => {
    process.env = { ...originalEnv };
  });

  afterEach(() => {
    process.env = originalEnv;
  });

  it('test_error_envelope_and_safe_user_mapping', async () => {
    const errRes = apiError('VALIDATION_ERROR', 'Bad input', 400, { email: ['Invalid email format'] });
    expect(errRes.status).toBe(400);
    const errJson = await errRes.json();
    expect(errJson).toEqual({
      error: {
        code: 'VALIDATION_ERROR',
        message: 'Bad input',
        details: { email: ['Invalid email format'] },
      },
    });

    const mockDbRow = {
      id: 'usr_123',
      name: 'Anas Ramouki',
      email: 'anas@example.com',
      role: 'analyst',
      jobTitle: 'Security Analyst',
      company: 'CyberCorp',
      whatsappPhone: '+212612345678',
      whatsappAlertsEnabled: true,
      emailAlertsEnabled: false,
      preferredLanguage: 'fr',
      password: 'secret_hash_should_be_omitted',
      internalSecretToken: 'should_be_omitted',
      createdAt: new Date('2026-01-01T12:00:00Z'),
      updatedAt: new Date('2026-01-02T12:00:00Z'),
    };

    const safe = toSafeUser(mockDbRow);
    expect(safe).toEqual({
      id: 'usr_123',
      email: 'anas@example.com',
      fullName: 'Anas Ramouki',
      role: 'analyst',
      jobTitle: 'Security Analyst',
      company: 'CyberCorp',
      whatsappPhone: '+212612345678',
      whatsappAlertsEnabled: true,
      emailAlertsEnabled: false,
      preferredLanguage: 'fr',
      createdAt: '2026-01-01T12:00:00.000Z',
      updatedAt: '2026-01-02T12:00:00.000Z',
    });
    expect((safe as any).password).toBeUndefined();
    expect((safe as any).internalSecretToken).toBeUndefined();
  });

  it('test_allowed_email_domains_parsing', () => {
    expect(isEmailDomainAllowed('user@dpg-cyber.com', 'dpg-cyber.com,example.ma')).toBe(true);
    expect(isEmailDomainAllowed('user@example.ma', 'dpg-cyber.com,example.ma')).toBe(true);
    expect(isEmailDomainAllowed('user@gmail.com', 'dpg-cyber.com,example.ma')).toBe(false);
    expect(isEmailDomainAllowed('user@gmail.com', '')).toBe(true);
    expect(isEmailDomainAllowed('user@gmail.com', undefined)).toBe(true);
  });

  it('test_proxy_cors_allowlist_and_preflight', () => {
    process.env.ALLOWED_ORIGINS = 'http://localhost:3000,http://localhost:5173';

    // 1. Allowed origin preflight
    const allowedReq = new NextRequest('http://localhost:3000/api/health', {
      method: 'OPTIONS',
      headers: {
        origin: 'http://localhost:5173',
      },
    });
    const preflightRes = proxy(allowedReq);
    expect(preflightRes.status).toBe(204);
    expect(preflightRes.headers.get('Access-Control-Allow-Origin')).toBe('http://localhost:5173');
    expect(preflightRes.headers.get('Access-Control-Allow-Credentials')).toBe('true');
    expect(preflightRes.headers.get('Vary')).toBe('Origin');
    expect(preflightRes.headers.get('X-Content-Type-Options')).toBe('nosniff');
    expect(preflightRes.headers.get('X-Frame-Options')).toBe('DENY');

    // 2. Disallowed origin preflight
    const disallowedReq = new NextRequest('http://localhost:3000/api/health', {
      method: 'OPTIONS',
      headers: {
        origin: 'http://malicious.site',
      },
    });
    const disallowedRes = proxy(disallowedReq);
    expect(disallowedRes.headers.get('Access-Control-Allow-Origin')).toBeNull();
  });
});
