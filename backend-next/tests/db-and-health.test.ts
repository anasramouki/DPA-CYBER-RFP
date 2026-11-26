import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import * as schema from '@/db/schema';
import { DEFAULT_SOURCES, seedSources } from '@/db/seed';

describe('Database Schema & Seed', () => {
  it('test_schema_exports_required_tables', () => {
    expect(schema.user).toBeDefined();
    expect(schema.session).toBeDefined();
    expect(schema.account).toBeDefined();
    expect(schema.verification).toBeDefined();
    expect(schema.sources).toBeDefined();
    expect(schema.tenders).toBeDefined();

    // Verify user columns
    expect(schema.user.id).toBeDefined();
    expect(schema.user.email).toBeDefined();
    expect(schema.user.name).toBeDefined();
    expect(schema.user.role).toBeDefined();
    expect(schema.user.jobTitle).toBeDefined();
    expect(schema.user.whatsappPhone).toBeDefined();
    expect(schema.user.whatsappAlertsEnabled).toBeDefined();
    expect(schema.user.emailAlertsEnabled).toBeDefined();
    expect(schema.user.preferredLanguage).toBeDefined();

    // Verify sources columns
    expect(schema.sources.id).toBeDefined();
    expect(schema.sources.slug).toBeDefined();
    expect(schema.sources.scraperType).toBeDefined();
    expect(schema.sources.isActive).toBeDefined();

    // Verify tenders columns
    expect(schema.tenders.id).toBeDefined();
    expect(schema.tenders.dedupHash).toBeDefined();
    expect(schema.tenders.sourceId).toBeDefined();
    expect(schema.tenders.isHighPriority).toBeDefined();
    expect(schema.tenders.matchedKeywords).toBeDefined();
  });

  it('test_seed_sources_contains_all_7_moroccan_portals', () => {
    const requiredSlugs = [
      'pmmp',
      'al-barid-bank',
      'sorec',
      'atlantic-re',
      'autoroutes-du-maroc',
      'laprophan',
      'ofppt',
    ];

    expect(DEFAULT_SOURCES.length).toBe(7);
    for (const slug of requiredSlugs) {
      const match = DEFAULT_SOURCES.find((s) => s.slug === slug);
      expect(match).toBeDefined();
      expect(match?.name).toBeTruthy();
      expect(match?.baseUrl).toMatch(/^https?:\/\//);
      expect(match?.scraperType).toBeTruthy();
    }
  });

  it('test_seed_sources_executes_idempotent_upsert', async () => {
    let insertedRows: any[] = [];
    const mockDb = {
      insert: vi.fn().mockReturnValue({
        values: vi.fn().mockImplementation((val) => {
          insertedRows = Array.isArray(val) ? val : [val];
          return {
            onConflictDoUpdate: vi.fn().mockResolvedValue({ rowCount: insertedRows.length }),
          };
        }),
      }),
    };

    const count = await seedSources(mockDb as any);
    expect(count).toBe(7);
    expect(mockDb.insert).toHaveBeenCalled();
  });
});

describe('Database Lazy Init & Health Route', () => {
  const originalEnv = { ...process.env };

  beforeEach(() => {
    process.env = { ...originalEnv };
  });

  afterEach(() => {
    process.env = originalEnv;
  });

  it('test_get_db_throws_only_on_call_when_missing_url', async () => {
    delete process.env.DATABASE_URL;
    const { getDb } = await import('@/db/index');
    expect(() => getDb()).toThrow(/DATABASE_URL/);
  });

  it('test_health_route_returns_200_when_db_ok_and_503_when_db_fails', async () => {
    const dbModule = await import('@/db/index');
    const { GET } = await import('@/app/api/health/route');

    // 1. Healthy check
    const spy = vi.spyOn(dbModule, 'checkDatabaseHealth').mockResolvedValueOnce(true);
    const okRes = await GET();
    expect(okRes.status).toBe(200);
    const okJson = await okRes.json();
    expect(okJson.status).toBe('ok');
    expect(okJson.database).toBe('connected');
    expect(okJson.timestamp).toBeTruthy();
    spy.mockRestore();

    // 2. Unhealthy check
    vi.spyOn(dbModule, 'checkDatabaseHealth').mockResolvedValueOnce(false);
    const failRes = await GET();
    expect(failRes.status).toBe(503);
    const failJson = await failRes.json();
    expect(failJson.error.code).toBe('INTERNAL_ERROR');
  });
});
