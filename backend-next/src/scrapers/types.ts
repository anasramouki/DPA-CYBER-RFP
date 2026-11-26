export interface ScrapedTender {
  externalRef: string | null;
  title: string;
  clientName: string;
  clientNormalized?: string | null;
  category?: string | null;
  publicationDate: Date | null;
  deadline: Date | null;
  directUrl: string;
  status: string;
  rawMetadata?: Record<string, unknown> | null;
}

export interface ScraperResult {
  sourceSlug: string;
  sourceName: string;
  tenders: ScrapedTender[];
  itemsFound: number;
  durationMs: number;
  error?: string | null;
}

export interface IScraper {
  slug: string;
  name: string;
  baseUrl: string;
  scrape(options?: { keywords?: string[] }): Promise<ScraperResult>;
}

export interface KeywordMatchResult {
  matchedKeywords: string[];
  relevanceScore: number;
  isHighPriority: boolean;
}
