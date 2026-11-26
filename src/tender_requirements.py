"""
Tender Submission Folder Requirements Generator
Provides exhaustive breakdowns for:
1. Administrative Folder (Dossier Administratif conforme Décret n° 2-22-431)
2. Technical Folder (Offre Technique & Grille des Profils / CVs Requis - inspired by DPA standard Excel matrices)
3. Financial Folder (Offre Financière, BPE, Acte d'engagement, DPGF)
"""
from typing import Dict, Any, List
from src.models import Tender

def get_submission_folder_data(tender: Tender) -> Dict[str, Any]:
    ref = tender.reference or ""
    title = (tender.title or "").lower()
    buyer = tender.buyer_name or ""
    sub_cat = tender.sub_category or ""
    caution = tender.provisional_guarantee or "Selon CPS"
    budget = tender.estimated_budget or 0.0

    # 1. Administrative Folder Items
    admin_items = [
        {
            "num": 1,
            "title": "Déclaration sur l’honneur",
            "requirement": "Remplir le modèle fourni dans le dossier d’appel d’offres, conforme à l'article 27 du décret n° 2-22-431. Mentionner l'exactitude des informations, non-interdiction de soumissionner et capacité juridique.",
            "format": "Original signé et cacheté par le représentant habilité DPA.",
            "mandatory": True,
            "dpa_ready": True
        },
        {
            "num": 2,
            "title": "Pouvoir du signataire",
            "requirement": "Document officiel justifiant que le signataire (M. John Doe) est habilité à engager la société DataProtech (DPA).",
            "format": "Copie certifiée conforme du PV d'assemblée / délégation de signature ou document juridique approprié.",
            "mandatory": True,
            "dpa_ready": True
        },
        {
            "num": 3,
            "title": "Cautionnement provisoire (Caution bancaire)",
            "requirement": f"Montant exigé : {caution}. Doit couvrir l'ensemble des lots soumissionnés sans réserve ni condition restrictive.",
            "format": "Original du récépissé de cautionnement provisoire ou caution bancaire personnelle et solidaire émise par un établissement agréé.",
            "mandatory": True,
            "dpa_ready": False
        },
        {
            "num": 4,
            "title": "Fiche d’identification de l'entreprise (DPA)",
            "requirement": "Fiche complète : Date de création, capital social, chiffre d’affaires des 3 derniers exercices, ICE (003102490000030), Identifiant Fiscal, Registre de Commerce et coordonnées officielles.",
            "format": "Document sur papier à entête officiel de la société DPA, signé et cacheté.",
            "mandatory": True,
            "dpa_ready": True
        },
        {
            "num": 5,
            "title": "Déclaration de l’effectif global",
            "requirement": "Indiquer l’effectif global permanent de la société DPA et la répartition des consultants, ingénieurs et cadres techniques.",
            "format": "Attestation d'effectif intégrée à la fiche société ou note séparée signée/cachetée.",
            "mandatory": True,
            "dpa_ready": True
        },
        {
            "num": 6,
            "title": "CPS + Règlement de Consultation (RC)",
            "requirement": "Joindre l'ensemble du Cahier des Prescriptions Spéciales (CPS) et le Règlement de Consultation (RC) de la consultation.",
            "format": "Paraphés sur chaque page et signés sur la dernière page avec la mention manuscrite obligatoire « Lu et approuvé ».",
            "mandatory": True,
            "dpa_ready": False
        },
        {
            "num": 7,
            "title": "Attestation Fiscale & Attestation CNSS",
            "requirement": "Attestation de régularité fiscale de la DGI et attestation de régularité des cotisations de la CNSS délivrées depuis moins d'un an.",
            "format": "Originaux ou copies certifiées conformes valides à la date d'ouverture des plis.",
            "mandatory": True,
            "dpa_ready": True
        }
    ]

    # 2. Technical Folder Items (Documents)
    tech_documents = [
        {
            "num": 1,
            "title": "Note sur les moyens humains et techniques",
            "requirement": "Présenter les moyens du concurrent et les principales prestations exécutées : lieu, date, nature, importance et rôle dans les missions.",
            "format": "Document technique signé et cacheté."
        },
        {
            "num": 2,
            "title": "Attestations de références similaires",
            "requirement": "Attestations délivrées par les maîtres d'ouvrage / bénéficiaires. Mettre en avant les références similaires (secteur financier, public, télécoms).",
            "format": "Copies des attestations de bonne exécution ; originales ou copies conformes selon disponibilité."
        },
        {
            "num": 3,
            "title": "Note de compréhension et analyse des enjeux",
            "requirement": "Compréhension approfondie du contexte, des objectifs stratégiques et des contraintes opérationnelles du marché.",
            "format": "Mémoire technique intégré à l'offre."
        },
        {
            "num": 4,
            "title": "Méthodologie détaillée + Plan de charge",
            "requirement": "Méthodologie détaillée, méthodes/frameworks, organisation de l’exécution, dispositif de delivery, priorisation et sécurisation de l'exécution.",
            "format": "Dans l’offre technique avec matrice RACI et gouvernance projet."
        },
        {
            "num": 5,
            "title": "Planning détaillé d'exécution",
            "requirement": "Planning de toutes les phases du projet, jalons de livraison, recettes techniques et transfert de compétences.",
            "format": "Planning Gantt intégré à l’offre technique."
        },
        {
            "num": 6,
            "title": "CVs détaillés des intervenants & Experts",
            "requirement": "CVs des profils proposés avec expérience prouvée, missions similaires et certifications correspondant aux profils demandés.",
            "format": "Un CV par consultant selon modèle normalisé."
        },
        {
            "num": 7,
            "title": "Grille détaillée des profils proposés (Annexe)",
            "requirement": "Compléter la grille : profil, nom/prénom, rôle, lot, expérience totale, expérience sectorielle, localisation, taux d’affectation en j/h.",
            "format": "Utiliser le modèle normalisé de l'Annexe technique."
        }
    ]

    # 3. Technical Profiles & CVs Table (Determined dynamically by RFP domain)
    # Match pure Data/AI governance projects without hijacking OT/SCADA security audits ("data integrity")
    is_ot_security = any(k in title for k in ["scada", "ot/", "ot ", "intrusion", "pentest", "firewall", "pare-feu", "ndr", "siem", "soc", "edr"])
    if not is_ot_security and any(k in title for k in ["data governance", "gouvernance data", "gouvernance des données", "intelligence artificielle", "big data", "data lake", "power bi"]):
        tech_profiles = [
            {
                "num": 1,
                "role": "Directeur de Mission",
                "min_exp": "12 ans",
                "key_skills": "Stratégie de transformation, Data/Cyber Strategy, connaissance du secteur Assurance/Réassurance/Finance",
                "certifications": "PMP, MBA ou équivalent",
                "lot": "Lots 1 & 2",
                "dpa_status": "Profil Qualifié DPA"
            },
            {
                "num": 2,
                "role": "Chef de Projet / PMO",
                "min_exp": "8 ans",
                "key_skills": "Gestion de projets complexes, méthodologie Agile, pilotage, risques, planning, comités, reporting",
                "certifications": "PMP, Prince2, Scrum Master",
                "lot": "Lots 1 & 2",
                "dpa_status": "Profil Qualifié DPA"
            },
            {
                "num": 3,
                "role": "Architecte Data & Expert Sécurité",
                "min_exp": "10 ans",
                "key_skills": "Architecture Cloud/Hybride, Data Lake, Data Mesh, flux d’intégration ETL/ELT, sécurité des données",
                "certifications": "TOGAF + certifications Cloud AWS/Azure/GCP",
                "lot": "Lot 1",
                "dpa_status": "Profil Qualifié DPA"
            },
            {
                "num": 4,
                "role": "Expert IA / Data Scientist",
                "min_exp": "5 ans",
                "key_skills": "Machine Learning, Python, modélisation des risques, algorithmique, LLM & IA Générative",
                "certifications": "Master IA / Certifications Spécialisées",
                "lot": "Lot 1",
                "dpa_status": "Vivier DPA"
            },
            {
                "num": 5,
                "role": "Data Engineer / Ingénieur Systèmes",
                "min_exp": "4 ans",
                "key_skills": "SQL avancé, Python, Spark, outils modernes d’ingestion, pipelines sécurisés",
                "certifications": "Certifications Cloud Data Engineer",
                "lot": "Lot 1",
                "dpa_status": "Profil Qualifié DPA"
            },
            {
                "num": 6,
                "role": "Expert Gouvernance Data & Conformité",
                "min_exp": "8 ans",
                "key_skills": "Frameworks de gouvernance, réglementation Data (CNDP, Loi 09-08, DNSSI), conception de modèles opérationnels",
                "certifications": "CDMP (DAMA), DCAM, CISA",
                "lot": "Lot 2",
                "dpa_status": "Profil Qualifié DPA"
            },
            {
                "num": 7,
                "role": "Expert Data Quality / Métadonnées",
                "min_exp": "5 ans",
                "key_skills": "Data Cataloging, modélisation conceptuelle, analyse de qualité et d'intégrité des données",
                "certifications": "DAMA CDMP ou équivalent",
                "lot": "Lot 2",
                "dpa_status": "Vivier DPA"
            },
            {
                "num": 8,
                "role": "Business Analyst Spécialisé Métier",
                "min_exp": "6 ans",
                "key_skills": "Processus métiers, analyse d'impact, recueil des besoins métiers, restitution analytique",
                "certifications": "CBAP / certification métier",
                "lot": "Lots 1 & 2",
                "dpa_status": "Profil Qualifié DPA"
            },
            {
                "num": 9,
                "role": "Expert Conduite du Changement & Formation",
                "min_exp": "6 ans",
                "key_skills": "Change Management, ingénierie pédagogique, communication interne, ateliers d'acculturation",
                "certifications": "PROSCI appréciée",
                "lot": "Lot 2",
                "dpa_status": "Profil Qualifié DPA"
            }
        ]
    elif any(k in title for k in ["dlp", "fuites de données", "endpoint", "cnss"]):
        # Specialization: Data Loss Prevention & Endpoint Security (e.g. CNSS AOOI150)
        tech_profiles = [
            {
                "num": 1,
                "role": "Directeur de Projet Sécurité de l'Information",
                "min_exp": "12 ans",
                "key_skills": "Supervision globale des projets SSI nationaux, gouvernance de la protection des données, relation comités",
                "certifications": "CISM, CISSP, PMP",
                "lot": "Lot Unique",
                "dpa_status": "Profil Qualifié DPA"
            },
            {
                "num": 2,
                "role": "Chef de Projet Déploiement DLP / PMO",
                "min_exp": "8 ans",
                "key_skills": "Pilotage du déploiement multi-sites, gestion des plannings, matrice des risques de déploiement d'agents DLP",
                "certifications": "PMP, Prince2, Scrum Master",
                "lot": "Lot Unique",
                "dpa_status": "Profil Qualifié DPA"
            },
            {
                "num": 3,
                "role": "Architecte Expert Solution DLP (Data Loss Prevention)",
                "min_exp": "10 ans",
                "key_skills": "Architecture DLP Endpoint, Network DLP, Discovery, intégration avec Active Directory et PKI, classification",
                "certifications": "Certifié Expert Constructeur (Symantec Knights / Forcepoint / Trellix)",
                "lot": "Lot Unique",
                "dpa_status": "Profil Qualifié DPA"
            },
            {
                "num": 4,
                "role": "Ingénieur Intégration Systèmes & Agents Endpoint",
                "min_exp": "5 ans",
                "key_skills": "Packaging et télédistribution d'agents (GPO, SCCM, Intune), troubleshooting compatibilité OS, filtrage",
                "certifications": "Microsoft Certified, Constructeur DLP Specialist",
                "lot": "Lot Unique",
                "dpa_status": "Profil Qualifié DPA"
            },
            {
                "num": 5,
                "role": "Expert Conformité CNDP & Réglementation DNSSI",
                "min_exp": "7 ans",
                "key_skills": "Conformité Loi 09-08 (protection des données personnelles CNDP), Directive Nationale DNSSI (DGSSI)",
                "certifications": "CISA, ISO 27001 Lead Implementer",
                "lot": "Lot Unique",
                "dpa_status": "Profil Qualifié DPA"
            },
            {
                "num": 6,
                "role": "Consultant Support Technique N3 & Transfert",
                "min_exp": "4 ans",
                "key_skills": "Support technique avancé, rédaction des procédures opérationnelles, formation des administrateurs CNSS",
                "certifications": "ITIL v4, Constructeur Certified",
                "lot": "Lot Unique",
                "dpa_status": "Vivier DPA"
            }
        ]
    elif any(k in title for k in ["firewall", "pare-feu", "réseau", "ddi", "intermédiaire", "oncf", "26s065"]):
        # Specialization: Next-Gen Firewalls & Network Infrastructure (e.g. ONCF 26S065)
        tech_profiles = [
            {
                "num": 1,
                "role": "Directeur de Projet Réseaux & Télécoms",
                "min_exp": "12 ans",
                "key_skills": "Direction de grands projets d'infrastructure réseaux et sécurité périmétrique pour opérateurs d'importance vitale",
                "certifications": "PMP, CCIE ou équivalent",
                "lot": "Lot Unique",
                "dpa_status": "Profil Qualifié DPA"
            },
            {
                "num": 2,
                "role": "Chef de Projet Déploiement Réseau",
                "min_exp": "8 ans",
                "key_skills": "Gestion des fenêtres de maintenance nocturnes, continuité de service ferroviaire, coordination des équipes",
                "certifications": "PMP, Prince2, ITIL",
                "lot": "Lot Unique",
                "dpa_status": "Profil Qualifié DPA"
            },
            {
                "num": 3,
                "role": "Architecte Cybersécurité & Firewalls Datacenter",
                "min_exp": "10 ans",
                "key_skills": "Architecture de pare-feu de Datacenter (NGFW), haute disponibilité actif/passif, micro-segmentation, Zero-Trust",
                "certifications": "Fortinet NSE 7/8, Check Point CCSE/CCSM, Palo Alto PCNSE",
                "lot": "Lot Unique",
                "dpa_status": "Profil Qualifié DPA"
            },
            {
                "num": 4,
                "role": "Expert Plateforme DDI (DNS, DHCP, IPAM)",
                "min_exp": "6 ans",
                "key_skills": "Conception et déploiement d'architectures DDI distribuées (Infoblox, EfficientIP, BlueCat), sécurisation DNS",
                "certifications": "DDI Certified Professional, CCNP Infrastructure",
                "lot": "Lot Unique",
                "dpa_status": "Profil Qualifié DPA"
            },
            {
                "num": 5,
                "role": "Ingénieur Intégration Réseau & Sécurité",
                "min_exp": "5 ans",
                "key_skills": "Migration de règles de filtrage firewall, routage BGP/OSPF, VPN IPsec/SSL, monitoring SNMP/Syslog",
                "certifications": "CCNP Security, Fortinet NSE 4/5",
                "lot": "Lot Unique",
                "dpa_status": "Profil Qualifié DPA"
            },
            {
                "num": 6,
                "role": "Consultant Tests, Recette & Assistance",
                "min_exp": "4 ans",
                "key_skills": "Plans de tests d'acceptation, bascule à chaud, tests de charge, transfert de compétences aux équipes",
                "certifications": "NSE Certified, ITIL",
                "lot": "Lot Unique",
                "dpa_status": "Vivier DPA"
            }
        ]
    else:
        # Default Cybersecurity / IT Procurement profile mix
        tech_profiles = [
            {
                "num": 1,
                "role": "Directeur de Mission / Consultant Principal",
                "min_exp": "12 ans",
                "key_skills": "Pilotage stratégique, gouvernance des SI, management des risques SSI, conformité réglementaire",
                "certifications": "PMP, CISM, CISSP",
                "lot": "Lot Unique",
                "dpa_status": "Profil Qualifié DPA"
            },
            {
                "num": 2,
                "role": "Chef de Projet / Lead Consultant",
                "min_exp": "8 ans",
                "key_skills": "Conduite de projets d'intégration, méthodologie Agile/Cycle en V, reporting et gestion des parties prenantes",
                "certifications": "PMP, Scrum Master, Prince2",
                "lot": "Lot Unique",
                "dpa_status": "Profil Qualifié DPA"
            },
            {
                "num": 3,
                "role": "Architecte Technique & Sécurité des Systèmes",
                "min_exp": "10 ans",
                "key_skills": "Conception d'architectures sécurisées, durcissement des systèmes, intégration aux infrastructures existantes",
                "certifications": "TOGAF, CISSP, Certifications Cloud",
                "lot": "Lot Unique",
                "dpa_status": "Profil Qualifié DPA"
            },
            {
                "num": 4,
                "role": "Expert Technique Métier Spécialisé",
                "min_exp": "5 ans",
                "key_skills": f"Maîtrise des technologies ciblées : {sub_cat or 'IT & Cybersécurité'}, implémentation et tests",
                "certifications": "Certifications professionnelles du domaine",
                "lot": "Lot Unique",
                "dpa_status": "Profil Qualifié DPA"
            },
            {
                "num": 5,
                "role": "Consultant Audit & Contrôle Qualité",
                "min_exp": "6 ans",
                "key_skills": "Audit de conformité (DNSSI, ISO 27001), validation des livrables techniques, assurance qualité",
                "certifications": "CISA, ISO 27001 Lead Auditor",
                "lot": "Lot Unique",
                "dpa_status": "Vivier DPA"
            },
            {
                "num": 6,
                "role": "Ingénieur Déploiement & Support Technique",
                "min_exp": "4 ans",
                "key_skills": "Mise en service opérationnelle, résolution d'incidents, rédaction documentation et formation",
                "certifications": "ITIL v4, Certifications constructeur",
                "lot": "Lot Unique",
                "dpa_status": "Profil Qualifié DPA"
            }
        ]

    for p in tech_profiles:
        p["profile_title"] = p.get("role", "")
        p["min_experience"] = p.get("min_exp", "")
        p["experience"] = p.get("min_exp", "")
        p["skills"] = p.get("key_skills", "")
        p["role"] = p.get("role", "")
        p["min_exp"] = p.get("min_exp", "")
        p["key_skills"] = p.get("key_skills", "")

    # 4. Financial Folder Items
    fin_budget_ht = round(budget / 1.2, 2) if budget > 0 else 0.0
    fin_tva = round(budget - fin_budget_ht, 2) if budget > 0 else 0.0

    financial_items = [
        {
            "num": 1,
            "title": "Acte d’Engagement (Modèle Réglementaire)",
            "requirement": "Compléter le modèle pour le lot concerné avec le montant de l’offre en chiffres et en lettres, montant HT, taux de TVA (20%) et montant TTC.",
            "format": "Original signé et cacheté par M. John Doe. Montants obligatoirement libellés en chiffres et en toutes lettres en dirhams marocains.",
            "mandatory": True
        },
        {
            "num": 2,
            "title": "Bordereau des Prix détaillé (BPE)",
            "requirement": "Compléter le bordereau de prix du lot concerné avec tous les prix unitaires hors taxes par rubrique ou prestation.",
            "format": "Signé et cacheté ; prix en MAD, en chiffres et en lettres, sans rature ni surcharge non visée.",
            "mandatory": True
        },
        {
            "num": 3,
            "title": "Sous-détail des prix unitaires (DPGF)",
            "requirement": "Décomposition détaillée des prix : coût des licences/matériels, taux journaliers des consultants/experts, frais de déplacement et marge.",
            "format": "Document financier de l'entreprise signé et cacheté.",
            "mandatory": True
        }
    ]

    return {
        "tender_id": tender.id,
        "tender_reference": tender.reference,
        "tender_title": tender.title,
        "buyer_name": tender.buyer_name,
        "portal_url": tender.source_url or "https://www.marchespublics.gov.ma",
        "caution_amount": caution,
        "administrative_items": admin_items,
        "technical_documents": tech_documents,
        "technical_profiles": tech_profiles,
        "tender_info": {
            "id": tender.id,
            "reference": tender.reference,
            "title": tender.title,
            "buyer_name": tender.buyer_name,
            "procedure_type": tender.procedure_type,
            "provisional_guarantee": caution,
            "estimated_budget": budget,
            "estimated_budget_ht": fin_budget_ht,
            "tva_20": fin_tva,
            "deadline": tender.deadline,
            "publication_date": tender.publication_date,
            "company_name": "DPA (DataProtech company)",
            "company_ice": "003102490000030",
            "company_signer": "John Doe"
        },
        "administrative_folder": {
            "title": "Dossier Administratif (Décret n° 2-22-431)",
            "description": "Pièces administratives et juridiques à préparer et déposer par DPA",
            "caution_amount": caution,
            "items": admin_items
        },
        "technical_folder": {
            "title": "Offre Technique & Profils / CVs Requis",
            "description": "Méthodologie, références et équipe d'experts mobilisée selon le Règlement de Consultation (RC)",
            "documents": tech_documents,
            "profiles": tech_profiles
        },
        "financial_folder": {
            "title": "Offre Financière (AE & BPE)",
            "description": "Chiffrage, bordereau des prix et engagements financiers contractuels",
            "budget_ttc": budget,
            "budget_ht": fin_budget_ht,
            "tva_amount": fin_tva,
            "budget_ttc_mad": f"{budget:,.2f} MAD".replace(",", " ") if budget > 0 else "Non précisé",
            "budget_ht_mad": f"{fin_budget_ht:,.2f} MAD".replace(",", " ") if budget > 0 else "Non précisé",
            "tva_mad": f"{fin_tva:,.2f} MAD".replace(",", " ") if budget > 0 else "Non précisé",
            "documents": financial_items,
            "items": financial_items
        }
    }
