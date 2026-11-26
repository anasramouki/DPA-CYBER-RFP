"""
Cybersecurity Keyword Classification Engine for CyberRFP Maroc
Supports French, English, and Arabic terminology.
Includes high-confidence positive terms, contextual terms, and negative filters.
"""
import re
import unicodedata
from typing import Dict, List, Optional, Set, Tuple


def normalize_text(text: str) -> str:
    """Lowercases, normalizes unicode, and removes special punctuation."""
    if not text:
        return ""
    nfkd = unicodedata.normalize('NFKD', text)
    stripped = "".join([c for c in nfkd if not unicodedata.combining(c)])
    cleaned = re.sub(r"[^\w\s\u0600-\u06FF\-_/]", " ", stripped).lower()
    return " ".join(cleaned.split())


# Definitive Cyber Keywords (Weight: 50-80 points each)
HIGH_CONFIDENCE_KEYWORDS: Dict[str, str] = {
    # French
    "cybersecurite": "CYBER_CORE",
    "cybersécurité": "CYBER_CORE",
    "securite des systemes d information": "SSI",
    "sécurité des systèmes d'information": "SSI",
    "securite de l information": "SSI",
    "securite informatique": "SSI",
    "securite du systeme d information": "SSI",
    "ssi": "SSI",
    "dnssi": "COMPLIANCE_DNSSI",
    "directive nationale de la securite": "COMPLIANCE_DNSSI",
    "loi 05 20": "COMPLIANCE_DNSSI",
    "loi 05-20": "COMPLIANCE_DNSSI",
    "loi 09 08": "COMPLIANCE_CNDP",
    "cndp": "COMPLIANCE_CNDP",
    "dgssi": "GOV_CYBER",
    "iso 27001": "ISO_27001",
    "iso 27002": "ISO_27001",
    "iso 22301": "PCA_PRA",
    "homologation de securite": "COMPLIANCE_DNSSI",
    "homologation ssi": "COMPLIANCE_DNSSI",
    
    # Audit & Pentest
    "test d intrusion": "AUDIT_PENTEST",
    "tests d intrusion": "AUDIT_PENTEST",
    "test d'intrusion": "AUDIT_PENTEST",
    "pentest": "AUDIT_PENTEST",
    "pentesting": "AUDIT_PENTEST",
    "audit de securite": "AUDIT_PENTEST",
    "audit de sécurité": "AUDIT_PENTEST",
    "audit ssi": "AUDIT_PENTEST",
    "audit organisationnel et technique de securite": "AUDIT_PENTEST",
    "analyse de vulnerabilite": "AUDIT_PENTEST",
    "scan de vulnerabilite": "AUDIT_PENTEST",
    "code review": "AUDIT_PENTEST",
    "revue de code": "AUDIT_PENTEST",

    # SOC & Monitoring
    "soc": "SOC_SIEM",
    "security operations center": "SOC_SIEM",
    "centre d operation de securite": "SOC_SIEM",
    "siem": "SOC_SIEM",
    "edr": "ENDPOINT_EDR",
    "xdr": "ENDPOINT_EDR",
    "ndr": "ENDPOINT_EDR",
    "network detection and response": "ENDPOINT_EDR",
    "mdr": "SOC_SIEM",
    "soar": "SOC_SIEM",
    "csirt": "INCIDENT_RESPONSE",
    "cert": "INCIDENT_RESPONSE",
    "gestion des incidents de securite": "INCIDENT_RESPONSE",
    "threat intelligence": "SOC_SIEM",
    "cti": "SOC_SIEM",
    "supervision securite": "SOC_SIEM",

    # Network & Perimeter
    "pare feu": "NETWORK_FIREWALL",
    "pare-feu": "NETWORK_FIREWALL",
    "firewall": "NETWORK_FIREWALL",
    "ngfw": "NETWORK_FIREWALL",
    "waf": "NETWORK_FIREWALL",
    "web application firewall": "NETWORK_FIREWALL",
    "ips": "NETWORK_FIREWALL",
    "ids": "NETWORK_FIREWALL",
    "ips ids": "NETWORK_FIREWALL",
    "antivirus": "ENDPOINT_EDR",
    "anti ddos": "NETWORK_FIREWALL",
    "ddos": "NETWORK_FIREWALL",
    "nac": "NETWORK_FIREWALL",
    "network access control": "NETWORK_FIREWALL",
    "bastion": "IAM_PAM",
    "pam": "IAM_PAM",
    "privileged access management": "IAM_PAM",
    "iam": "IAM_PAM",
    "identity and access": "IAM_PAM",
    "mfa": "IAM_PAM",
    "authentification forte": "IAM_PAM",
    "gestion des identites": "IAM_PAM",
    "pki": "ENCRYPTION_PKI",
    "hsm": "ENCRYPTION_PKI",
    "chiffrement": "ENCRYPTION_PKI",
    "cryptographie": "ENCRYPTION_PKI",
    "signature electronique": "ENCRYPTION_PKI",
    "dlp": "DATA_PROTECTION",
    "data loss prevention": "DATA_PROTECTION",
    "vpn": "NETWORK_FIREWALL",
    "zero trust": "NETWORK_FIREWALL",
    "ztna": "NETWORK_FIREWALL",

    # Continuity & Storage (when tied to security/resilience)
    "pca": "PCA_PRA",
    "pra": "PCA_PRA",
    "plan de continuite": "PCA_PRA",
    "plan de reprise d activite": "PCA_PRA",
    "sauvegarde immuable": "BACKUP_STORAGE",

    # Arabic terms
    "الأمن السيبراني": "CYBER_CORE",
    "أمن نظم المعلومات": "SSI",
    "أمن المعلومات": "SSI",
    "السلامة المعلوماتية": "SSI",
    "جدار الحماية": "NETWORK_FIREWALL",
    "تدقيق أمني": "AUDIT_PENTEST",
    "اختبار الاختراق": "AUDIT_PENTEST",
    "مركز العمليات الأمنية": "SOC_SIEM",
    "إدارة الهويات": "IAM_PAM",
    "التشفير": "ENCRYPTION_PKI",
    "استمرارية النشاط": "PCA_PRA"
}

# Moderate / Contextual IT terms (Weight: 15-25 points each)
CONTEXTUAL_IT_KEYWORDS: Set[str] = {
    "sauvegarde",
    "sauvegardes",
    "backup",
    "baie de stockage",
    "datacenter",
    "data center",
    "serveurs",
    "infrastructure informatique",
    "reseau informatique",
    "commutateurs",
    "switch",
    "routeurs",
    "sd-wan",
    "supervision reseau",
    "virtualisation",
    "cloud",
    "active directory",
    "ldap",
    "messagerie",
    "intégrité des données",
    "infogerance",
    "tma",
}

# Strong Negative Terms (False Positive Reducers)
NEGATIVE_KEYWORDS: Set[str] = {
    "incendie",
    "securite incendie",
    "sécurité incendie",
    "extincteur",
    "extincteurs",
    "desenfumage",
    "désenfumage",
    "gardiennage",
    "surveillance humaine",
    "securite routiere",
    "sécurité routière",
    "securite physique",
    "agents de securite",
    "maitres-chiens",
    "maitre chien",
    "nettoyage",
    "nettoiement",
    "proprete",
    "lutte contre les incendies",
    "portiers",
    "patrouille",
    "gardien",
    "gardienne",
    "vigile",
    "vigiles",
    "blanchissage",
    "bâtiment",
    "plomberie",
    "peinture",
    "étanchéité",
    "travaux de voirie",
    "génie civil",
    "espaces verts",
    "jardinage",
    "restauration",
    "repas",
    "traiteur",
    "mobilier de bureau",
    "véhicules",
    "voitures",
    "carburant",
}


def classify_text_rules(title: str, text_excerpt: str = "") -> Tuple[str, int, str, List[str]]:
    """
    Evaluates title and optional document excerpt against cybersecurity rules.
    Returns:
      (relevance_category, relevance_score, sub_category, matched_keywords)
      where relevance_category is 'CYBERSECURITY', 'MAYBE', or 'NOT_RELEVANT'
    """
    full_text = f"{title} {text_excerpt}".lower()
    norm_full = normalize_text(full_text)
    norm_title = normalize_text(title)

    matched_positives: List[str] = []
    matched_negatives: List[str] = []
    sub_categories_votes: Dict[str, int] = {}
    score = 0

    # 1. Check High-Confidence Keywords
    for kw, subcat in HIGH_CONFIDENCE_KEYWORDS.items():
        norm_kw = normalize_text(kw)
        # Search in title (3x weight) or body
        if len(norm_kw) <= 4:
            pattern = rf"\b{re.escape(norm_kw)}\b"
            in_title = bool(re.search(pattern, norm_title))
            in_body = bool(re.search(pattern, norm_full))
        else:
            in_title = norm_kw in norm_title
            in_body = norm_kw in norm_full

        if in_title:
            matched_positives.append(kw)
            score += 55
            sub_categories_votes[subcat] = sub_categories_votes.get(subcat, 0) + 3
        elif in_body:
            matched_positives.append(kw)
            score += 35
            sub_categories_votes[subcat] = sub_categories_votes.get(subcat, 0) + 1

    # 2. Check Contextual IT Keywords
    for kw in CONTEXTUAL_IT_KEYWORDS:
        norm_kw = normalize_text(kw)
        if len(norm_kw) <= 4:
            pattern = rf"\b{re.escape(norm_kw)}\b"
            in_title = bool(re.search(pattern, norm_title))
            in_body = bool(re.search(pattern, norm_full))
        else:
            in_title = norm_kw in norm_title
            in_body = norm_kw in norm_full

        if in_title:
            matched_positives.append(kw)
            score += 15
        elif in_body:
            score += 5

    # 3. Check Negative Keywords
    for neg in NEGATIVE_KEYWORDS:
        norm_neg = normalize_text(neg)
        if len(norm_neg) <= 4:
            pattern = rf"\b{re.escape(norm_neg)}\b"
            match_found = bool(re.search(pattern, norm_full))
        else:
            match_found = norm_neg in norm_full

        if match_found:
            matched_negatives.append(neg)

    # Apply negative penalties
    if matched_negatives:
        # If there are strong cybersecurity keywords, reduce penalty (e.g. IT datacenter physical security)
        has_strong_cyber = any(
            HIGH_CONFIDENCE_KEYWORDS.get(k) in [
                "CYBER_CORE", "SSI", "AUDIT_PENTEST", "SOC_SIEM", "COMPLIANCE_DNSSI",
                "NETWORK_FIREWALL", "IAM_PAM", "ENDPOINT_EDR", "ENCRYPTION_PKI"
            ]
            for k in matched_positives
        )
        if has_strong_cyber:
            score = max(0, score - 25)
        else:
            # Pure negative (e.g. gardiennage, incendie, batiment) -> penalize heavily
            score = max(0, score - 70)

    # Cap score at 100
    score = min(100, max(0, score))

    # Determine category
    if score >= 60:
        category = "CYBERSECURITY"
    elif score >= 25:
        category = "MAYBE"
    else:
        category = "NOT_RELEVANT"

    # Determine winning sub-category
    if sub_categories_votes:
        top_subcat = max(sub_categories_votes.items(), key=lambda x: x[1])[0]
    else:
        if any("sauvegarde" in k or "backup" in k for k in matched_positives):
            top_subcat = "BACKUP_STORAGE"
        elif any("reseau" in k or "switch" in k for k in matched_positives):
            top_subcat = "NETWORK_INFRA"
        elif category == "CYBERSECURITY":
            top_subcat = "SECURITY_OTHER"
        else:
            top_subcat = "GENERAL_IT" if score >= 25 else "NOT_RELEVANT"

    # Human-readable subcategory
    subcat_labels = {
        "CYBER_CORE": "Cybersécurité Globale",
        "SSI": "Sécurité des SI (SSI)",
        "AUDIT_PENTEST": "Audit & Tests d'intrusion (Pentest)",
        "SOC_SIEM": "SOC & Supervision SIEM",
        "ENDPOINT_EDR": "Sécurité Endpoint & EDR/XDR",
        "NETWORK_FIREWALL": "Pare-feu & Sécurité Réseau / WAF",
        "IAM_PAM": "Gestion des Identités (IAM/PAM)",
        "ENCRYPTION_PKI": "Chiffrement & PKI / HSM",
        "COMPLIANCE_DNSSI": "Conformité DNSSI & Homologation",
        "ISO_27001": "Gouvernance & ISO 27001",
        "PCA_PRA": "Résilience & PCA / PRA",
        "BACKUP_STORAGE": "Sauvegarde & Stockage Sécurisé",
        "INCIDENT_RESPONSE": "Réponse aux Incidents (CSIRT)",
        "DATA_PROTECTION": "Protection des Données & DLP",
        "SECURITY_OTHER": "Sécurité IT Générale",
        "NETWORK_INFRA": "Infrastructure Réseau",
        "GENERAL_IT": "Informatique Générale",
        "NOT_RELEVANT": "Non Pertinent"
    }
    subcat_display = subcat_labels.get(top_subcat, "Sécurité Informatique")

    return category, score, subcat_display, matched_positives
