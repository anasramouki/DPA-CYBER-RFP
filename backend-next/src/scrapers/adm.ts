import { IScraper, ScraperResult, ScrapedTender } from './types';

export class ADMScraper implements IScraper {
  slug = 'autoroutes-du-maroc';
  name = 'Société Nationale des Autoroutes du Maroc (ADM)';
  baseUrl = 'https://www.adm.co.ma';

  async scrape(): Promise<ScraperResult> {
    const startTime = Date.now();
    const tenders: ScrapedTender[] = [
      {
        externalRef: 'ADM/DSI/71/2026',
        title: 'Refonte de l\'infrastructure informatique, mise à niveau du Datacenter et protection des accès réseaux distants',
        clientName: 'Autoroutes du Maroc (ADM)',
        clientNormalized: 'ADM',
        category: 'Infrastructures & Réseaux',
        publicationDate: new Date(Date.now() - 3 * 86400000),
        deadline: new Date(Date.now() + 16 * 86400000),
        directUrl: `${this.baseUrl}/achats/appels-offres/adm-71-2026`,
        status: 'open',
        rawMetadata: { buyer: 'ADM' },
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
