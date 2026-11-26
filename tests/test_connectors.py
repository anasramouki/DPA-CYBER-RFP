"""
Parser and Connector Tests using Saved Fixtures
"""
import os
import sys
import pytest
from bs4 import BeautifulSoup

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.connectors.pmmp import PMMPConnector
from src.connectors.albaridbank import AlBaridBankConnector
from src.connectors.generic import GenericConfigurableConnector
from src.classifier.engine import ClassifierEngine


FIXTURES_DIR = os.path.join(os.path.dirname(__file__), "fixtures")


def test_pmmp_html_parser_fixture():
    fixture_path = os.path.join(FIXTURES_DIR, "pmmp_sample.html")
    with open(fixture_path, "r", encoding="utf-8") as f:
        html = f.read()

    soup = BeautifulSoup(html, "html.parser")
    box = soup.find("div", class_="generalBox")
    assert box is not None

    connector = PMMPConnector(fetch_details=False)
    # Parse box without network calls
    tender = connector._parse_general_box(box, client=None)

    assert tender is not None
    assert tender.reference == "AOO/CYBER/2026/05"
    assert tender.procedure_type == "AOO"
    assert "OFPPT" in tender.buyer_name
    assert tender.is_priority_buyer is True
    assert tender.priority_badge == "OFPPT (Prioritaire)"
    assert tender.estimated_budget == 3200000.0
    assert tender.deadline == "2027-01-15 11:00:00"
    assert "SOC, SIEM et EDR" in tender.title


def test_abb_html_parser_fixture():
    fixture_path = os.path.join(FIXTURES_DIR, "abb_sample.html")
    with open(fixture_path, "r", encoding="utf-8") as f:
        html = f.read()

    soup = BeautifulSoup(html, "html.parser")
    table = soup.find("table", class_="list-table")
    assert table is not None

    connector = AlBaridBankConnector(fetch_details=False)
    rows = table.find_all("tr")
    cols = rows[1].find_all("td")

    assert len(cols) == 6
    title = cols[3].get_text(strip=True)
    assert "NDR" in title
    assert cols[2].get_text(strip=True) == "Al Barid Bank"
    assert cols[5].get_text(strip=True) == "26/11/2026 11:00"


def test_generic_configurable_connector():
    config = {
        "id": "gen_anrt",
        "name": "ANRT Maroc",
        "base_url": "https://anrt.ma",
        "listing_url": "https://anrt.ma/appels-offres",
        "item_selector": "div.tender-row",
        "title_selector": "h4.title",
        "ref_selector": "span.ref",
        "deadline_selector": "span.date",
        "budget_selector": "span.amount"
    }
    connector = GenericConfigurableConnector(config)
    assert connector.connector_id == "gen_anrt"
    assert connector.name == "ANRT Maroc"
    assert connector.item_selector == "div.tender-row"
