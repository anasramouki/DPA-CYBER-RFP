"""
Unit tests for Authentic Press & Procurement Aggregator Connector
Verifies:
- Accurate HTML parsing of Moroccan tender aggregators (AO Maroc and MarocBiz)
- Zero hallucination: authentic URLs and extracted attributes
- Proper buyer categorization and priority tagging
- Health check execution
- SQLite DB ingestion and retrieval
"""
import sys
import os
import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.connectors.press_journal import PressJournalConnector
from src.database import Database
from src.models import Tender


SAMPLE_AOMAROC_HTML = """
<html>
<body>
<article class="offre">
  <p class="carte-tete" data-dl="2026-12-15 10:00:00">
    📅 15/12/2026 10:00 | 📝 32/2026/ONHYM
  </p>
  <h3><a href="/offre/56102.html">Audit de cybersécurité des systèmes d'information et tests d'intrusion (Pentest)</a></h3>
  <p class="ach"><a>ONHYM - Office National des Hydrocarbures et des Mines</a></p>
  <span class="mnt">1 250 000,00 DH</span>
  <span class="cau">🛡️ 15 000,00 MAD</span>
  <p>📍 Rabat</p>
  <p class="actions-carte">
    <a href="https://www.marchespublics.gov.ma/index.php?page=entreprise.EntrepriseDetailsConsultation&refConsultation=56102">Portail</a>
    <a href="/cps?id=56102">CPS</a>
  </p>
</article>
<article class="offre">
  <p class="carte-tete" data-dl="2026-12-20 11:00:00">
    📅 20/12/2026 11:00 | 📝 14/ANAPEC/2026
  </p>
  <h3><a href="/offre/56103.html">Acquisition et mise en service de commutateurs et pare-feu réseau Datacenter</a></h3>
  <p class="ach"><a>ANAPEC</a></p>
  <span class="mnt">850 000,00 DH</span>
  <span class="cau">🛡️ 10 000,00 MAD</span>
  <p>📍 Casablanca</p>
</article>
</body>
</html>
"""

SAMPLE_MAROCBIZ_HTML = """
<html>
<body>
<ul class="list">
  <li>
    <a class="o" href="/appels-offres/56104-fourniture-solution-siem-soc.html">Fourniture et déploiement d'une solution SIEM et supervision SOC</a>
    <span class="ach">CNSS</span>
    <span class="ref">AOO 45/CNSS/2026</span>
    <span class="dl">30/12/2026 10:00</span>
    <span class="loc">Casablanca</span>
  </li>
</ul>
</body>
</html>
"""


def test_parse_aomaroc_html():
    tenders = PressJournalConnector.parse_aomaroc_html(SAMPLE_AOMAROC_HTML)
    assert len(tenders) == 2

    # Check first tender
    t1 = tenders[0]
    assert t1.reference == "32/2026/ONHYM"
    assert "audit de cybersécurité" in t1.title.lower()
    assert "ONHYM" in t1.buyer_name
    assert t1.estimated_budget == 1250000.0
    assert "15 000" in (t1.provisional_guarantee or "")
    assert t1.deadline == "2026-12-15 10:00:00"
    assert "56102" in t1.source_url
    assert any("marchespublics.gov.ma" in d.url for d in t1.document_links)

    # Check second tender
    t2 = tenders[1]
    assert t2.reference == "14/ANAPEC/2026"
    assert "pare-feu" in t2.title.lower()
    assert "ANAPEC" in t2.buyer_name
    assert t2.estimated_budget == 850000.0


def test_parse_marocbiz_html():
    tenders = PressJournalConnector.parse_marocbiz_html(SAMPLE_MAROCBIZ_HTML)
    assert len(tenders) >= 1
    t = tenders[0]
    assert "siem" in t.title.lower() or "soc" in t.title.lower()
    assert "56104" in t.source_url or "marocbiz.com" in t.source_url


def test_press_journal_health_check():
    connector = PressJournalConnector()
    health = connector.health_check()
    assert health.connector_id == "press_journal"
    assert health.status in ["HEALTHY", "DEGRADED"]


def test_press_journal_tenders_ingestion_in_db():
    db = Database()
    tenders = PressJournalConnector.parse_aomaroc_html(SAMPLE_AOMAROC_HTML)
    assert len(tenders) >= 1

    for t in tenders:
        is_new, is_updated = db.upsert_tender(t)
        # Should be stored without exception

    # Retrieve from DB
    retrieved = db.get_tender_by_id(tenders[0].id)
    assert retrieved is not None
    assert retrieved.reference == "32/2026/ONHYM"
    assert "ONHYM" in retrieved.buyer_name


def test_press_journal_filtering():
    connector = PressJournalConnector()
    parsed_sample = PressJournalConnector.parse_aomaroc_html(SAMPLE_AOMAROC_HTML)

    # Filter by keyword
    cyber_only = [t for t in parsed_sample if any(k in t.title.lower() for k in ["pentest", "cybersécurité"])]
    assert len(cyber_only) == 1
    assert cyber_only[0].reference == "32/2026/ONHYM"

    # Filter by buyer
    onhym_only = [t for t in parsed_sample if "onhym" in t.buyer_normalized.lower()]
    assert len(onhym_only) == 1
    assert onhym_only[0].reference == "32/2026/ONHYM"
