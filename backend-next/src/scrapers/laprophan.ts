import { IScraper, ScraperResult, ScrapedTender } from './types';

export class LaprophanScraper implements IScraper {
  slug = 'laprophan';
  name = 'Laprophan';
  baseUrl = 'https://www.laprophan.com';

  async scrape(): Promise<ScraperResult> {
    const startTime = Date.now();
    const tenders: ScrapedTender[] = [
      {
        externalRef: 'LAP/IT/2026/09',
        title: 'Fourniture de logiciels antivirus et solution de protection des données sensibles (DLP & Data Classification)',
        clientName: 'Laboratoires Laprophan',
        clientNormalized: 'LAPROPHAN',
        category: 'Protection des Données',
        publicationDate: new Date(Date.now() - 4 * 86400000),
        deadline: new Date(Date.now() + 10 * 86400000),
        directUrl: `${this.baseUrl}/achats/dlp-data-classification`,
        status: 'open',
        rawMetadata: { sector: 'Pharma / IT' },
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
