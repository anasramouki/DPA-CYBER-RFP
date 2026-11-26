import 'dotenv/config';
import { eq } from 'drizzle-orm';
import { getDb } from './index';
import { sources as sourcesTable, tenders as tendersTable } from './schema';
import { matchKeywords, generateDedupHash } from '../scrapers/utils';

async function seedPMMPCyber() {
  console.log('Seeding pure PMMP Cybersecurity tenders...');
  const db = getDb();

  const [pmmpSource] = await db
    .select()
    .from(sourcesTable)
    .where(eq(sourcesTable.slug, 'pmmp'))
    .limit(1);

  if (!pmmpSource) {
    console.error('PMMP source not found');
    return;
  }

  const cyberTenders = [
    {
      externalRef: '37/2026/DGI',
      title: 'L’ACQUISITION, L’INSTALLATION, LA CONFIGURATION ET LA MISE EN ŒUVRE D’UNE SOLUTION DE PROTECTION DES BASES DE DONNÉES ORACLE, POUR LE COMPTE DE LA DIRECTION GENERALE DES IMPOTS, (Lot Unique).',
      clientName: 'Direction Générale des Impôts (DGI) - Ministère de l’Économie et des Finances',
      deadline: new Date('2026-12-15T10:00:00Z'),
      directUrl: 'https://www.marchespublics.gov.ma/?page=entreprise.EntrepriseDetailsConsultation&refConsultation=1049314&orgAcronyme=g8e&retraits',
    },
    {
      externalRef: '43/2026/DGSSI',
      title: 'Mise en place d\'un centre de surveillance opérationnelle de sécurité (SOC managé) avec détection et réponse aux menaces EDR/XDR',
      clientName: 'Direction Générale de la Sécurité des Systèmes d\'Information (DGSSI)',
      deadline: new Date('2026-12-08T11:00:00Z'),
      directUrl: 'https://www.marchespublics.gov.ma/?page=entreprise.EntrepriseDetailsConsultation&refConsultation=1054321&orgAcronyme=DGSSI',
    },
    {
      externalRef: '12/2026/CNSS',
      title: 'Acquisition et intégration d\'une solution de classification des données (Data Classification) et prévention des fuites DLP Forcepoint',
      clientName: 'Caisse Nationale de Sécurité Sociale (CNSS)',
      deadline: new Date('2026-12-22T10:30:00Z'),
      directUrl: 'https://www.marchespublics.gov.ma/?page=entreprise.EntrepriseDetailsConsultation&refConsultation=1051226&orgAcronyme=CNSS',
    },
    {
      externalRef: '88/2026/TGR',
      title: 'Fourniture et renouvellement des licences de pare-feu (Firewalls NGFW de nouvelle génération) et protection Endpoint pour le Trésor',
      clientName: 'Trésorerie Générale du Royaume (TGR)',
      deadline: new Date('2026-12-05T10:00:00Z'),
      directUrl: 'https://www.marchespublics.gov.ma/?page=entreprise.EntrepriseDetailsConsultation&refConsultation=1048890&orgAcronyme=TGR',
    },
    {
      externalRef: '05/2026/MTN',
      title: 'Audit de sécurité des systèmes d\'information, tests d\'intrusion externes et pentest des plateformes applicatives étatiques',
      clientName: 'Ministère de la Transition Numérique et de la Réforme de l\'Administration (MTNRA)',
      deadline: new Date('2026-12-02T10:30:00Z'),
      directUrl: 'https://www.marchespublics.gov.ma/?page=entreprise.EntrepriseDetailsConsultation&refConsultation=1055002&orgAcronyme=MTNRA',
    },
    {
      externalRef: '21/2026/BAM',
      title: 'Renouvellement et extension de la solution de corrélation d\'événements de sécurité SIEM et de gestion des accès à privilèges (PAM/Bastion)',
      clientName: 'Bank Al-Maghrib (Banque Centrale du Maroc)',
      deadline: new Date('2026-12-18T10:00:00Z'),
      directUrl: 'https://www.marchespublics.gov.ma/?page=entreprise.EntrepriseDetailsConsultation&refConsultation=1052140&orgAcronyme=BAM',
    },
  ];

  for (const item of cyberTenders) {
    const { matchedKeywords, relevanceScore, isHighPriority } = matchKeywords(item.title);
    const dedupHash = generateDedupHash('pmmp', item.externalRef, item.title);

    await db
      .insert(tendersTable)
      .values({
        dedupHash,
        sourceId: pmmpSource.id,
        externalRef: item.externalRef,
        title: item.title,
        clientName: item.clientName,
        clientNormalized: item.clientName.slice(0, 50).toUpperCase(),
        category: 'Cybersécurité & SSI',
        publicationDate: new Date(),
        deadline: item.deadline,
        directUrl: item.directUrl,
        status: 'open',
        isHighPriority,
        matchedKeywords,
        relevanceScore,
        rawMetadata: { portal: 'PMMP', verifiedCyber: true },
      })
      .onConflictDoUpdate({
        target: tendersTable.dedupHash,
        set: {
          matchedKeywords,
          relevanceScore,
          isHighPriority,
          category: 'Cybersécurité & SSI',
        },
      });

    console.log(`✓ Inserted/Updated PMMP cyber tender: [${item.externalRef}] -> ${matchedKeywords.join(', ')}`);
  }

  console.log('Done seeding PMMP cyber tenders.');
}

seedPMMPCyber()
  .then(() => process.exit(0))
  .catch((err) => {
    console.error('Error:', err);
    process.exit(1);
  });
