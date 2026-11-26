import { describe, it, expect } from 'vitest';
import { NextRequest } from 'next/server';
import { GET as getTenders } from '@/app/api/tenders/route';
import { GET as getSources } from '@/app/api/sources/route';

describe('Milestone 3: Tenders & Sources Endpoints', () => {
  it('test_get_sources_returns_list_with_stats', async () => {
    const res = await getSources();
    expect(res.status).toBe(200);
    const json = await res.json();
    expect(Array.isArray(json.sources)).toBe(true);
    expect(json.total).toBeGreaterThanOrEqual(7);
    expect(json.active).toBeGreaterThanOrEqual(7);
  });

  it('test_get_tenders_supports_filters_and_pagination', async () => {
    // 1. Unfiltered page 1
    const req1 = new NextRequest('http://localhost:3000/api/tenders?page=1&limit=5');
    const res1 = await getTenders(req1);
    expect(res1.status).toBe(200);
    const json1 = await res1.json();
    expect(Array.isArray(json1.items)).toBe(true);
    expect(json1.pagination.page).toBe(1);
    expect(json1.pagination.limit).toBe(5);

    // 2. High priority filter
    const req2 = new NextRequest('http://localhost:3000/api/tenders?priority=high');
    const res2 = await getTenders(req2);
    expect(res2.status).toBe(200);
    const json2 = await res2.json();
    for (const item of json2.items) {
      expect(item.isHighPriority).toBe(true);
    }
  });
});
