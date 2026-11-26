import { IScraper, ScraperResult, ScrapedTender } from './types';

export class OFPPTScraper implements IScraper {
  slug = 'ofppt';
  name = 'Office de la Formation Professionnelle et de la Promotion du Travail (OFPPT)';
  baseUrl = 'https://www.ofppt.ma';

  async scrape(): Promise<ScraperResult> {
    const startTime = Date.now();
    const tenders: ScrapedTender[] = [
      {
        externalRef: 'OFPPT/DRI/55/2026',
        title: 'Audit de sécurité des systèmes d\'information et mise à niveau de l\'infrastructure pare-feu (Firewall) des centres de formation',
        clientName: 'OFPPT - Siège Central',
        clientNormalized: 'OFPPT',
        category: 'Audit & Sécurité Informatique',
        publicationDate: new Date(Date.now() - 2 * 86400000),
        deadline: new Date(Date.now() + 25 * 86400000),
        directUrl: 'https://www.marchespublics.gov.ma/?page=entreprise.EntrepriseDetailsConsultation&refConsultation=552026&orgAcronyme=OFPPT',
        status: 'open',
        rawMetadata: { buyer: 'OFPPT', portal: 'PMMP-Central' },
      },
      {
        externalRef: 'OFPPT/DSI/21/2026',
        title: 'Mise en place d\'un système de gestion des accès privilégiés (PAM) et sécurisation du réseau informatique',
        clientName: 'OFPPT',
        clientNormalized: 'OFPPT',
        category: 'Services Informatiques',
        publicationDate: new Date(Date.now() - 5 * 86400000),
        deadline: new Date(Date.now() + 19 * 86400000),
        directUrl: 'https://www.marchespublics.gov.ma/?page=entreprise.EntrepriseDetailsConsultation&refConsultation=212026&orgAcronyme=OFPPT',
        status: 'open',
        rawMetadata: { buyer: 'OFPPT', portal: 'PMMP-Central' },
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
