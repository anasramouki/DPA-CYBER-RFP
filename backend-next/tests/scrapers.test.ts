import { describe, it, expect } from 'vitest';
import {
  cleanText,
  parseMoroccanDate,
  generateDedupHash,
  matchKeywords,
} from '@/scrapers/utils';
import { orchestrator } from '@/scrapers/orchestrator';

describe('Milestone 2: Scraping Engine & Normalization Tests', () => {
  it('test_clean_text_removes_prefixes_and_pua_glyphs', () => {
    const raw = 'Objet : \ue001 Fourniture de pare-feu et monitoring SOC ';
    expect(cleanText(raw)).toBe('Fourniture de pare-feu et monitoring SOC');

    const buyer = 'Acheteur public :  OFPPT - Direction Régionale';
    expect(cleanText(buyer)).toBe('OFPPT - Direction Régionale');
  });

  it('test_date_normalization_handles_various_moroccan_formats', () => {
    // DD/MM/YYYY HH:mm
    const d1 = parseMoroccanDate('23/11/2026 11:00');
    expect(d1).not.toBeNull();
    expect(d1?.getUTCFullYear()).toBe(2026);
    expect(d1?.getUTCMonth()).toBe(10); // Nov is month 10 (0-indexed)
    expect(d1?.getUTCDate()).toBe(23);

    // Textual French: "Mar 09 Fév 2027 10:30"
    const d2 = parseMoroccanDate('Mar 09 Fév 2027 10:30');
    expect(d2).not.toBeNull();
    expect(d2?.getUTCFullYear()).toBe(2027);
    expect(d2?.getUTCMonth()).toBe(1); // Feb is month 1
    expect(d2?.getUTCDate()).toBe(9);

    // ISO: 2026-12-31
    const d3 = parseMoroccanDate('2026-12-31');
    expect(d3).not.toBeNull();
    expect(d3?.getUTCFullYear()).toBe(2026);
  });

  it('test_keyword_matching_and_high_priority_detection', () => {
    // 1. Cyber RFP with SOC, DLP, Forcepoint
    const cyberTitle = 'Acquisition d\'une solution de classification des données Data Classification et DLP Forcepoint avec monitoring SOC';
    const res1 = matchKeywords(cyberTitle);
    expect(res1.isHighPriority).toBe(true);
    expect(res1.matchedKeywords).toContain('dlp');
    expect(res1.matchedKeywords).toContain('forcepoint');
    expect(res1.matchedKeywords).toContain('soc');
    expect(res1.relevanceScore).toBeGreaterThanOrEqual(70);

    // 2. Generic IT without High Priority trigger
    const itTitle = 'Travaux de câblage et réseau informatique local';
    const res2 = matchKeywords(itTitle);
    expect(res2.isHighPriority).toBe(false);
    expect(res2.matchedKeywords).toContain('informatique');
    expect(res2.matchedKeywords).toContain('réseau');

    // 3. Non-IT RFP
    const nonIt = 'Travaux d\'aménagement paysager et espaces verts';
    const res3 = matchKeywords(nonIt);
    expect(res3.matchedKeywords.length).toBe(0);
    expect(res3.relevanceScore).toBe(0);
    expect(res3.isHighPriority).toBe(false);
  });

  it('test_deduplication_hash_idempotency', () => {
    const hash1 = generateDedupHash('pmmp', 'AO-43/2026', 'Solution SOC et EDR');
    const hash2 = generateDedupHash('pmmp', 'AO-43/2026', 'Solution SOC et EDR');
    const hash3 = generateDedupHash('pmmp', 'ao-43/2026', 'solution soc et edr');

    expect(hash1).toBe(hash2);
    expect(hash1).toBe(hash3);

    const hashOther = generateDedupHash('pmmp', 'AO-44/2026', 'Solution SOC et EDR');
    expect(hash1).not.toBe(hashOther);
  });

  it('test_all_7_scrapers_registered_and_contract_valid', async () => {
    // Mock global fetch to return quickly in unit test environment
    const originalFetch = globalThis.fetch;
    globalThis.fetch = async () => {
      throw new Error('Network disabled in unit test');
    };

    try {
      const scrapers = orchestrator.listScrapers();
      expect(scrapers.length).toBe(7);

      const slugs = scrapers.map((s) => s.slug);
      expect(slugs).toContain('pmmp');
      expect(slugs).toContain('al-barid-bank');
      expect(slugs).toContain('ofppt');
      expect(slugs).toContain('sorec');
      expect(slugs).toContain('atlantic-re');
      expect(slugs).toContain('autoroutes-du-maroc');
      expect(slugs).toContain('laprophan');

      for (const scraper of scrapers) {
        const res = await scraper.scrape();
        expect(res.sourceSlug).toBe(scraper.slug);
        expect(res.tenders.length).toBeGreaterThan(0);
        for (const t of res.tenders) {
          expect(t.title).toBeTruthy();
          expect(t.clientName).toBeTruthy();
          expect(t.directUrl).toMatch(/^https?:\/\//);
          expect(t.status).toBe('open');
        }
      }
    } finally {
      globalThis.fetch = originalFetch;
    }
  });
});
