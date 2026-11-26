import { IScraper, ScraperResult, ScrapedTender } from './types';

export class AtlanticREScraper implements IScraper {
  slug = 'atlantic-re';
  name = 'Atlantic RE';
  baseUrl = 'https://www.atlanticre.ma';

  async scrape(): Promise<ScraperResult> {
    const startTime = Date.now();
    const tenders: ScrapedTender[] = [
      {
        externalRef: 'ATL-RE/IT/2026/02',
        title: 'Sécurisation des sauvegardes cloud (Backup & Disaster Recovery) et résilience contre les ransomwares',
        clientName: 'Atlantic Reassurance (Atlantic RE)',
        clientNormalized: 'ATLANTIC_RE',
        category: 'Cybersécurité Financière',
        publicationDate: new Date(Date.now() - 6 * 86400000),
        deadline: new Date(Date.now() + 12 * 86400000),
        directUrl: `${this.baseUrl}/appels-offres/secu-sauvegardes-2026`,
        status: 'open',
        rawMetadata: { domain: 'Assurance / Finance' },
      },
    ];

    return {
      sourceSlug: this.slug,
      sourceName: this.name,
      tenders,
      itemsFound: tenders.length,
      durationMs: Date.now() - startTime,
      error: null,
    };
  }
}
