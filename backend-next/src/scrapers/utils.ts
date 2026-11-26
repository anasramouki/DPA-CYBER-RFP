import crypto from 'crypto';
import { KeywordMatchResult } from './types';

export const DEFAULT_CYBER_KEYWORDS = [
  'cybersécurité',
  'cybersecurite',
  'cyber',
  'informatique',
  'soc',
  'dlp',
  'forcepoint',
  'endpoint',
  'data classification',
  'firewall',
  'pare-feu',
  'siem',
  'edr',
  'xdr',
  'antivirus',
  'sauvegarde',
  'backup',
  'sécurité des systèmes d\'information',
  'securite',
  'audit de sécurité',
  'pentest',
  'intrusion',
  'datacenter',
  'serveur',
  'réseau',
  'reseau',
  'chiffrement',
  'cryptographie',
  'iam',
  'pam',
  'bastion',
];

export const HIGH_PRIORITY_KEYWORDS = [
  'cybersécurité',
  'cybersecurite',
  'soc',
  'dlp',
  'forcepoint',
  'endpoint',
  'data classification',
  'siem',
  'edr',
  'xdr',
  'pare-feu',
  'firewall',
  'audit de sécurité',
  'pentest',
];

const FRENCH_MONTHS: Record<string, number> = {
  janv: 0,
  janvier: 0,
  fev: 1,
  fevr: 1,
  fevrier: 1,
  mars: 2,
  avr: 3,
  avril: 3,
  mai: 4,
  juin: 5,
  juil: 6,
  juillet: 6,
  aout: 7,
  sept: 8,
  septembre: 8,
  oct: 9,
  octobre: 9,
  nov: 10,
  novembre: 10,
  dec: 11,
  decembre: 11,
};

export function cleanText(text: string | null | undefined): string {
  if (!text) return '';
  let cleaned = text.replace(/[\ue000-\uf8ff]/g, ' ');
  cleaned = cleaned.replace(/^\s*(?:Objet|Acheteur\s+public|Référence|Reference)\s*:\s*/i, '');
  cleaned = cleaned.replace(/^[\s\-•·*:\ue000-\uf8ff]+/, '');
  return cleaned.replace(/\s+/g, ' ').trim();
}

export function parseMoroccanDate(dateStr: string | null | undefined): Date | null {
  if (!dateStr) return null;
  const s = dateStr.trim();

  // Try standard ISO or YYYY-MM-DD
  const isoMatch = s.match(/^(\d{4})-(\d{2})-(\d{2})(?:[T\s](\d{2}):(\d{2}))?/);
  if (isoMatch) {
    const [, year, month, day, hour, min] = isoMatch;
    return new Date(
      Date.UTC(
        Number(year),
        Number(month) - 1,
        Number(day),
        hour ? Number(hour) : 10,
        min ? Number(min) : 0
      )
    );
  }

  // Format: DD/MM/YYYY or DD/MM/YYYY HH:mm
  const slashMatch = s.match(/(\d{1,2})\/(\d{1,2})\/(\d{4})(?:[^\d]+(\d{1,2}):(\d{2}))?/);
  if (slashMatch) {
    const [, day, month, year, hour, min] = slashMatch;
    return new Date(
      Date.UTC(
        Number(year),
        Number(month) - 1,
        Number(day),
        hour ? Number(hour) : 10,
        min ? Number(min) : 0
      )
    );
  }

  // Format: optional day name (e.g. "Mar", "Lun") followed by day month year: "Mar 09 Fév 2027 10:30"
  const textMatch = s.match(/(?:[a-zA-Z\u00C0-\u017F]+\.?\s+)?(\d{1,2})\s+([a-zA-Z\u00C0-\u017F]+)\s+(\d{4})(?:[^\d]+(\d{1,2}):(\d{2}))?/i);
  if (textMatch) {
    const [, day, monthRaw, year, hour, min] = textMatch;
    const cleanMonth = monthRaw
      .toLowerCase()
      .normalize('NFD')
      .replace(/[\u0300-\u036f]/g, '');

    const prefix = cleanMonth.slice(0, 4);
    const prefix3 = cleanMonth.slice(0, 3);
    const monthIndex = FRENCH_MONTHS[cleanMonth] ?? FRENCH_MONTHS[prefix] ?? FRENCH_MONTHS[prefix3];

    if (monthIndex !== undefined) {
      return new Date(
        Date.UTC(
          Number(year),
          monthIndex,
          Number(day),
          hour ? Number(hour) : 10,
          min ? Number(min) : 0
        )
      );
    }
  }

  const parsed = Date.parse(s);
  return isNaN(parsed) ? null : new Date(parsed);
}

export function generateDedupHash(sourceSlug: string, externalRefOrUrl: string, title: string): string {
  const normTitle = title.toLowerCase().replace(/[^a-z0-9]/g, '').slice(0, 80);
  const normRef = externalRefOrUrl.toLowerCase().trim();
  const input = `${sourceSlug}|${normRef}|${normTitle}`;
  return crypto.createHash('sha256').update(input, 'utf8').digest('hex');
}

export function matchKeywords(text: string, customKeywords?: string[]): KeywordMatchResult {
  const lowerText = text.toLowerCase();
  const allKeywords = customKeywords && customKeywords.length > 0 ? customKeywords : DEFAULT_CYBER_KEYWORDS;
  const matched = new Set<string>();

  for (const kw of allKeywords) {
    const cleanKw = kw.toLowerCase().trim();
    if (cleanKw.length === 0) continue;
    // Word boundary or substring for acronyms like SOC, DLP, EDR
    const escaped = cleanKw.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
    const regex = new RegExp(`(?:^|[\\s,;:'"()/-])${escaped}(?:$|[\\s,;:'"()/-])`, 'i');
    if (regex.test(lowerText) || lowerText.includes(cleanKw)) {
      matched.add(cleanKw);
    }
  }

  const matchedKeywords = Array.from(matched);
  const isHighPriority = matchedKeywords.some((kw) =>
    HIGH_PRIORITY_KEYWORDS.includes(kw.toLowerCase())
  );

  let relevanceScore = matchedKeywords.length * 20;
  if (isHighPriority) {
    relevanceScore += 50;
  }
  relevanceScore = Math.min(relevanceScore, 100);

  return {
    matchedKeywords,
    relevanceScore,
    isHighPriority,
  };
}
