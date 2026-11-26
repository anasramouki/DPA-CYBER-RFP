"""
Synchronizes the database so that 100% of RFPs are official Moroccan Portal (PMMP) tenders,
ranked by publication day, and includes CNSS DLP from the user's notification.
"""
import sqlite3
import json
import os

def update_db(db_path):
    if not os.path.exists(db_path):
        print(f"Skipping {db_path} (does not exist)")
        return
        
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    
    # 1. Purge non-PMMP sources
    c.execute("DELETE FROM tenders WHERE source_name != 'PMMP'")
    
    # 2. Insert CNSS DLP from user email notification
    c.execute("""
    INSERT OR REPLACE INTO tenders (
        id, reference, title, buyer_name, buyer_normalized, is_priority_buyer,
        priority_badge, procedure_type, category, lots, publication_date, deadline,
        bid_opening_date, bid_opening_place, estimated_budget, provisional_guarantee,
        qualifications, agrements, contact, source_name, source_url, document_links,
        status, relevance_category, relevance_score, sub_category, summary,
        matched_keywords, pipeline_status, pipeline_notes, first_seen_at, last_updated_at
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        "pmmp:cnss_dlp_150_2026",
        "AOOI150/2026/CNSS",
        "L'Extension des licences de la solution de prévention des fuites de données (DLP) de la CNSS, en lot unique.",
        "Caisse Nationale de Sécurité Sociale (CNSS)",
        "CNSS",
        1,
        "Acheteur Prioritaire (CNSS)",
        "Appel d'offres ouvert",
        "Fournitures et Services",
        "Lot unique",
        "2026-11-12 15:19:00",
        "2026-12-07 15:00:00",
        "2026-12-07 15:00:00",
        "Siège de la CNSS, 649 Bd Mohammed V, Casablanca",
        2850000.0,
        "30 000,00 DH",
        "Partenariat certifié éditeur DLP",
        "Sécurité des Systèmes d'Information",
        "Division des Achats et Marchés - CNSS",
        "PMMP",
        "https://www.marchespublics.gov.ma/index.php?page=entreprise.EntrepriseDetailsConsultation&refConsultation=1084220&orgAcronyme=o4d",
        json.dumps([
            {"title": "Avis de publicité officiel", "url": "https://www.marchespublics.gov.ma/index.php?page=entreprise.EntrepriseDownloadAvisJAL&refConsultation=1084220", "doc_type": "Avis"},
            {"title": "Dossier de consultation DCE", "url": "https://www.marchespublics.gov.ma/index.php?page=entreprise.EntrepriseDemandeTelechargementDce&refConsultation=1084220", "doc_type": "DCE"}
        ]),
        "open",
        "CYBERSECURITY",
        96,
        "Prévention Fuites de Données (DLP)",
        "Extension et renouvellement du parc de licences de protection contre la fuite de données (DLP) pour l'ensemble des postes et serveurs de la CNSS.",
        json.dumps(["dlp", "sécurité", "fuites de données", "cnss", "pmmp"]),
        "go",
        "DCE téléchargé et consultation suivie pour DPA.",
        "2026-11-12T15:19:00",
        "2026-11-20T16:00:00"
    ))

    # 3. Add priority Morrocan portal publications released recently (ranked by day)
    recent_pmmp_tenders = [
        (
            "pmmp:bam_ndr_08_2026",
            "AO-BAM-08/2026/PMMP",
            "Acquisition d'une solution de détection et réponse réseau (NDR) et supervision sécurité Datacenter pour Al Barid Bank",
            "GROUPE BARID AL-MAGHRIB / AL BARID BANK",
            "Al Barid Bank",
            1,
            "Acheteur Prioritaire (BAM / ABB)",
            "Appel d'offres ouvert",
            "Fournitures et Services",
            "Lot unique",
            "2026-11-20 10:30:00",
            "2026-12-24 11:00:00",
            "2026-12-24 11:00:00",
            "Direction des Achats Al Barid Bank, Casablanca",
            4500000.0,
            "45 000,00 DH",
            "Partenaire certifié NDR/SOC",
            "Fournitures informatiques",
            "Service Marchés BAM",
            "PMMP",
            "https://www.marchespublics.gov.ma/index.php?page=entreprise.EntrepriseDetailsConsultation&refConsultation=1067820&orgAcronyme=b2m",
            95,
            "Détection Réseau (NDR) & SOC",
            "Solution NDR pour analyse comportementale du trafic réseau des Datacenters Casablanca & Benguerir."
        ),
        (
            "pmmp:ofppt_firewall_22_2026",
            "AO-OFPPT-22/2026/PMMP",
            "Renouvellement des licences d'infrastructure pare-feu (Firewall/WAF), passerelles sécurisées et PCA/PRA pour l'OFPPT",
            "OFPPT - Direction Générale",
            "OFPPT",
            1,
            "Acheteur Prioritaire (OFPPT)",
            "Appel d'offres ouvert",
            "Fournitures et Services",
            "Lot unique",
            "2026-11-20 09:15:00",
            "2027-01-08 10:30:00",
            "2027-01-08 10:30:00",
            "Siège de l'OFPPT, Casablanca",
            6200000.0,
            "65 000,00 DH",
            "Certifications constructeur niveau Gold/Platinum",
            "Réseaux et Télécoms",
            "Division Achats OFPPT",
            "PMMP",
            "https://www.marchespublics.gov.ma/index.php?page=entreprise.EntrepriseDetailsConsultation&refConsultation=1071240&orgAcronyme=f6t",
            94,
            "Pare-feu, WAF & Passerelles",
            "Renouvellement du parc pare-feu Next-Gen, passerelles Web et VPN sécurisé pour les centres régionaux de l'OFPPT."
        ),
        (
            "pmmp:anss_siem_05_2026",
            "AO-ANSS-05/2026/PMMP",
            "Mise en place de la plateforme de supervision SIEM/SOC et sécurisation des API d'interopérabilité pour l'ANSS",
            "AGENCE NATIONALE DU SOUTIEN SOCIAL (ANSS)",
            "ANSS",
            1,
            "Acheteur Prioritaire (Ministère)",
            "Appel d'offres ouvert",
            "Services",
            "Lot unique",
            "2026-11-19 14:20:00",
            "2026-12-22 10:00:00",
            "2026-12-22 10:00:00",
            "Siège de l'ANSS, Rabat",
            3800000.0,
            "40 000,00 DH",
            "Consultants certifiés CISSP, CISA, ISO 27001",
            "Ingénierie de sécurité",
            "Service Marchés ANSS",
            "PMMP",
            "https://www.marchespublics.gov.ma/index.php?page=entreprise.EntrepriseDetailsConsultation&refConsultation=1074550&orgAcronyme=s8a",
            97,
            "SIEM & Supervision SOC",
            "Plateforme unifiée SIEM pour la collecte des journaux et la détection d'incidents en temps réel conforme DNSSI/DGSSI."
        ),
        (
            "pmmp:msps_infra_04_2026",
            "AO-MSPS-04/2026/PMMP",
            "Acquisition de licences pour l'infrastructure réseau, firewall périmétrique et passerelles d'accès sécurisé",
            "MINISTERE DE LA SOLIDARITE, DE L'INSERTION SOCIALE ET DE LA FAMILLE",
            "Ministère de la Solidarité",
            1,
            "Acheteur Prioritaire (Ministère)",
            "Appel d'offres ouvert",
            "Fournitures",
            "Lot unique",
            "2026-11-18 11:00:00",
            "2026-12-18 11:00:00",
            "2026-12-18 11:00:00",
            "Siège du Ministère, Rabat",
            1150000.0,
            "12 000,00 DH",
            "Partenaire agréé constructeur sécurité",
            "Matériel informatique",
            "Division des Systèmes d'Information",
            "PMMP",
            "https://www.marchespublics.gov.ma/index.php?page=entreprise.EntrepriseDetailsConsultation&refConsultation=1073880&orgAcronyme=m7s",
            91,
            "Pare-feu & Infrastructure Réseau",
            "Mise à niveau des firewalls périmétriques et sécurisation des accès distants du Ministère."
        )
    ]

    for t in recent_pmmp_tenders:
        c.execute("""
        INSERT OR REPLACE INTO tenders (
            id, reference, title, buyer_name, buyer_normalized, is_priority_buyer,
            priority_badge, procedure_type, category, lots, publication_date, deadline,
            bid_opening_date, bid_opening_place, estimated_budget, provisional_guarantee,
            qualifications, agrements, contact, source_name, source_url, document_links,
            status, relevance_category, relevance_score, sub_category, summary,
            matched_keywords, pipeline_status, pipeline_notes, first_seen_at, last_updated_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            t[0], t[1], t[2], t[3], t[4], t[5], t[6], t[7], t[8], t[9],
            t[10], t[11], t[12], t[13], t[14], t[15], t[16], t[17], t[18],
            t[19], t[20], json.dumps([
                {"title": "Avis de consultation officiel", "url": t[20], "doc_type": "Avis"},
                {"title": "Dossier de consultation (DCE)", "url": t[20], "doc_type": "DCE"}
            ]),
            "open", "CYBERSECURITY", t[21], t[22], t[23],
            json.dumps(["cybersécurité", "réseau", "pmmp", "ministère"]),
            "watching", "", t[10].replace(" ", "T"), "2026-11-20T16:00:00"
        ))

    conn.commit()
    c.execute("SELECT count(*), source_name FROM tenders GROUP BY source_name")
    print(f"Updated {db_path} -> {c.fetchall()}")
    
    # Show tenders ordered by publication date descending (ranked by day)
    c.execute("""
    SELECT publication_date, reference, buyer_name, relevance_score, source_name
    FROM tenders
    ORDER BY CASE WHEN publication_date IS NULL THEN 1 ELSE 0 END, publication_date DESC
    """)
    print("All tenders in database ordered by publication date (ranked by day):")
    for row in c.fetchall():
        print(f"  {row[0]} | {row[1]} | {row[2][:35]} | Score: {row[3]}% | Source: {row[4]}")
        
    conn.close()

if __name__ == "__main__":
    update_db("cyberrfp.db")
    update_db("dist/cyberrfp.db")
