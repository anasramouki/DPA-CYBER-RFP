"""
Normalization utilities for Moroccan dates, amounts, and buyer names.
"""
import re
from datetime import datetime
from typing import Optional, Tuple

FRENCH_MONTHS = {
    "janv": "01", "jan": "01", "janvier": "01",
    "févr": "02", "fevr": "02", "fév": "02", "fev": "02", "février": "02", "fevrier": "02",
    "mars": "03", "mar": "03",
    "avr": "04", "avril": "04",
    "mai": "05",
    "juin": "06",
    "juil": "07", "juillet": "07",
    "août": "08", "aout": "08",
    "sept": "09", "sep": "09", "septembre": "09",
    "oct": "10", "octobre": "10",
    "nov": "11", "novembre": "11",
    "déc": "12", "dec": "12", "décembre": "12", "decembre": "12",
}

ARABIC_MONTHS = {
    "يناير": "01", "فبراير": "02", "مارس": "03", "أبريل": "04", "ابريل": "04",
    "ماي": "05", "مايو": "05", "يونيو": "06", "يوليوز": "07", "يوليو": "07",
    "غشت": "08", "أغسطس": "08", "شتنبر": "09", "سبتمبر": "09",
    "أكتوبر": "10", "اكتوبر": "10", "نونبر": "11", "نوفمبر": "11",
    "دجنبر": "12", "ديسمبر": "12"
}


def parse_moroccan_amount(amount_str: Optional[str]) -> float:
    """
    Parses Moroccan amounts like '40 931 655,07', '800 000,00 MAD', '1 250 000 DH'.
    Returns float in Dirhams.
    """
    if not amount_str:
        return 0.0
    text = str(amount_str).strip()
    cleaned = re.sub(r"[^\d,\.]", "", text)
    if not cleaned:
        return 0.0
    
    # Handle Moroccan decimal separator (comma)
    if "," in cleaned and "." in cleaned:
        if cleaned.rfind(",") > cleaned.rfind("."):
            cleaned = cleaned.replace(".", "").replace(",", ".")
        else:
            cleaned = cleaned.replace(",", "")
    elif "," in cleaned:
        cleaned = cleaned.replace(",", ".")
    
    try:
        return float(cleaned)
    except ValueError:
        return 0.0


def parse_moroccan_datetime(dt_str: Optional[str]) -> Optional[str]:
    """
    Parses various Moroccan portal date representations into SQL YYYY-MM-DD HH:MM:SS.
    Examples:
    - 'Mar 09 Fév 2027' + '10:30'
    - '09/02/2027 10:30'
    - '28/10/2026'
    - 'Mer 28 Oct 2026 11:42'
    - '2026-11-23 11:00'
    """
    if not dt_str:
        return None
    raw = dt_str.strip()
    
    # Check ISO format
    if re.match(r"^\d{4}-\d{2}-\d{2}", raw):
        if len(raw) == 10:
            return f"{raw} 10:00:00"
        return raw

    # Match numeric DD/MM/YYYY [HH:MM[:SS]]
    m_num = re.search(r"\b(\d{1,2})/(\d{1,2})/(\d{4})(?:\s+(\d{1,2}:\d{2}(?::\d{2})?))?", raw)
    if m_num:
        day = int(m_num.group(1))
        month = int(m_num.group(2))
        year = int(m_num.group(3))
        time_part = m_num.group(4) or "10:00:00"
        if len(time_part) == 5:
            time_part = f"{time_part}:00"
        return f"{year:04d}-{month:02d}-{day:02d} {time_part}"
    
    # Match French textual month e.g. '09 Fév 2027' or 'Mar 09 Fév 2027 10:30'
    m_fr = re.search(r"(\d{1,2})\s+([A-Za-z\u00C0-\u017F]+)\s+(\d{4})(?:\s+(\d{1,2}:\d{2}(?::\d{2})?))?", raw)
    if m_fr:
        day = int(m_fr.group(1))
        month_word = m_fr.group(2).lower()
        year = int(m_fr.group(3))
        time_part = m_fr.group(4) or "10:00:00"
        if len(time_part) == 5:
            time_part = f"{time_part}:00"
        
        # Match month
        month = None
        for k, v in FRENCH_MONTHS.items():
            if month_word.startswith(k):
                month = v
                break
        if month:
            return f"{year:04d}-{month}-{day:02d} {time_part}"

    return raw
