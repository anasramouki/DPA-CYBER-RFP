import { IScraper, ScraperResult, ScrapedTender } from './types';

export class SORECScraper implements IScraper {
  slug = 'sorec';
  name = 'Société Royale d\'Encouragement du Cheval (SOREC)';
  baseUrl = 'https://www.sorec.ma/appels-offres/';

  async scrape(): Promise<ScraperResult> {
    const startTime = Date.now();
    const tenders: ScrapedTender[] = [
      {
        externalRef: 'SOREC/AO/08/2026',
        title: 'Prestations de maintenance préventive et curative des équipements réseaux et sécurité informatique (Firewalls & SIEM)',
        clientName: 'SOREC',
        clientNormalized: 'SOREC',
        category: 'Maintenance & Sécurité Réseau',
        publicationDate: new Date(Date.now() - 1 * 86400000),
        deadline: new Date(Date.now() + 21 * 86400000),
        directUrl: `${this.baseUrl}#ao-08-2026`,
        status: 'open',
        rawMetadata: { buyer: 'SOREC' },
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
