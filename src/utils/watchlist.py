"""
Buyer Watchlist and Fuzzy Matcher for CyberRFP Maroc
Supports French, Arabic, and acronym matching for Moroccan public buyers.
"""
import re
import unicodedata
from typing import Dict, List, Optional, Tuple
from src.models import WatchlistBuyer

DEFAULT_PRIORITY_WATCHLIST: List[WatchlistBuyer] = [
    WatchlistBuyer(
        name="OFPPT",
        normalized_keywords=[
            "ofppt",
            "office de la formation professionnelle",
            "promotion du travail",
            "مكتب التكوين المهني",
            "إنعاش الشغل"
        ],
        badge_label="OFPPT (Prioritaire)",
        category="Office Public"
    ),
    WatchlistBuyer(
        name="Al Barid Bank",
        normalized_keywords=[
            "al barid bank",
            "barid al-maghrib",
            "barid bank",
            "barid cash",
            "groupe barid",
            "poste maroc",
            "بريد بنك",
            "بريد المغرب"
        ],
        badge_label="Al Barid Bank (Prioritaire)",
        category="Banque Publique"
    ),
    WatchlistBuyer(
        name="SOREC",
        normalized_keywords=[
            "sorec",
            "encouragement du cheval",
            "societe royale d'encouragement du cheval",
            "الشركة الملكية لتشجيع الفرس"
        ],
        badge_label="SOREC (Prioritaire)",
        category="Société d'État"
    ),
    WatchlistBuyer(
        name="DGSSI",
        normalized_keywords=[
            "dgssi",
            "direction generale de la securite des systemes d'information",
            "sécurité des systèmes d'information",
            "المديرية العامة لأمن نظم المعلومات"
        ],
        badge_label="DGSSI (Sécurité d'État)",
        category="Défense & Sécurité"
    ),
    WatchlistBuyer(
        name="ANRT",
        normalized_keywords=[
            "anrt",
            "agence nationale de reglementation des telecommunications",
            "الوكالة الوطنية لتقنين المواصلات"
        ],
        badge_label="ANRT (Régulateur)",
        category="Agence Publique"
    ),
    WatchlistBuyer(
        name="ADD",
        normalized_keywords=[
            "add",
            "agence de developpement du digital",
            "développement du digital",
            "وكالة التنمية الرقمية"
        ],
        badge_label="ADD (Digital)",
        category="Agence Publique"
    ),
    WatchlistBuyer(
        name="CNSS",
        normalized_keywords=[
            "cnss",
            "caisse nationale de securite sociale",
            "sécurité sociale",
            "الصندوق الوطني للضمان الاجتماعي"
        ],
        badge_label="CNSS",
        category="Établissement Public"
    ),
    WatchlistBuyer(
        name="CDG",
        normalized_keywords=[
            "cdg",
            "caisse de depot et de gestion",
            "dépôt et de gestion",
            "صندوق الإيداع والتدبير"
        ],
        badge_label="CDG",
        category="Institution Financière"
    ),
    WatchlistBuyer(
        name="ONEE",
        normalized_keywords=[
            "onee",
            "office national de l'electricite et de l'eau potable",
            "المكتب الوطني للكهرباء والماء الصالح للشرب"
        ],
        badge_label="ONEE",
        category="Office Public"
    ),
    WatchlistBuyer(
        name="ONDA",
        normalized_keywords=[
            "onda",
            "office national des aeroports",
            "المكتب الوطني للمطارات"
        ],
        badge_label="ONDA",
        category="Office Public"
    ),
    WatchlistBuyer(
        name="Bank Al-Maghrib",
        normalized_keywords=[
            "bank al-maghrib",
            "banque centrale",
            "bam",
            "بنك المغرب"
        ],
        badge_label="Bank Al-Maghrib",
        category="Banque Centrale"
    ),
    WatchlistBuyer(
        name="Atlantic Re",
        normalized_keywords=[
            "atlantic re",
            "scr",
            "societe centrale de reassurance",
            "centrale de reassurance",
            "reassurance cdg",
            "الشركة المركزية لإعادة التأمين",
            "أتلانتيك آر إي"
        ],
        badge_label="Atlantic Re (Prioritaire CDG)",
        category="Réassurance & Finance (CDG)"
    ),
    WatchlistBuyer(
        name="Laprophan",
        normalized_keywords=[
            "laprophan",
            "laboratoires pharmaceutiques d'afrique du nord",
            "laboratoire laprophan",
            "pharmaceutiques afrique du nord",
            "لابروفان",
            "مختبرات لابروفان"
        ],
        badge_label="Laprophan (Pharma & Santé)",
        category="Industrie Pharmaceutique"
    )
]


def strip_accents_and_normalize(text: str) -> str:
    """Normalize string: lowercase, strip accents, remove excess punctuation."""
    if not text:
        return ""
    nfkd = unicodedata.normalize('NFKD', text)
    stripped = "".join([c for c in nfkd if not unicodedata.combining(c)])
    cleaned = re.sub(r"[^\w\s\u0600-\u06FF]", " ", stripped).lower()
    return " ".join(cleaned.split())


def match_buyer_watchlist(
    buyer_raw: str,
    watchlist: Optional[List[WatchlistBuyer]] = None
) -> Tuple[bool, Optional[str], Optional[str]]:
    """
    Fuzzy checks if buyer_raw matches any buyer in the priority watchlist.
    Returns: (is_priority, matched_buyer_name, badge_label)
    """
    if not buyer_raw:
        return False, None, None
        
    norm_buyer = strip_accents_and_normalize(buyer_raw)
    buyers = watchlist or DEFAULT_PRIORITY_WATCHLIST
    
    for buyer in buyers:
        for kw in buyer.normalized_keywords:
            norm_kw = strip_accents_and_normalize(kw)
            # Match either as whole word or substring for distinctive acronyms/phrases
            if len(norm_kw) <= 4:
                # Short acronyms: word boundary
                pattern = rf"\b{re.escape(norm_kw)}\b"
                if re.search(pattern, norm_buyer):
                    return True, buyer.name, buyer.badge_label
            else:
                if norm_kw in norm_buyer:
                    return True, buyer.name, buyer.badge_label
                    
    return False, None, None
