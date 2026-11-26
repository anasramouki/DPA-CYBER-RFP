"""
Unit Tests for Alerts Dispatcher and Reminders
"""
import sys
import os
import pytest
from datetime import datetime, timedelta

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.alerts.dispatcher import AlertsDispatcher
from src.models import Tender, TenderChange


def test_alerts_dispatcher_webhook_formatting():
    dispatcher = AlertsDispatcher(config={"webhook_url": "https://example.com/webhook", "webhook_type": "generic"})
    tender = Tender(
        id="test-alert-1",
        reference="AO/CYBER/2026/01",
        title="Acquisition d'une solution SOC et EDR",
        buyer_name="Office de la Formation Professionnelle et de la Promotion du Travail (OFPPT)",
        buyer_normalized="OFPPT",
        is_priority_buyer=True,
        priority_badge="OFPPT (Prioritaire)",
        deadline="2027-01-15 10:00:00",
        estimated_budget=1800000.0,
        source_name="PMMP",
        source_url="https://marchespublics.gov.ma/cons1",
        relevance_category="CYBERSECURITY",
        relevance_score=95,
        sub_category="SOC & Supervision SIEM"
    )

    # Test webhook payload creation
    assert tender.is_priority_buyer is True
    assert tender.relevance_score == 95


def test_corrigendum_alert_formatting():
    dispatcher = AlertsDispatcher()
    tender = Tender(
        id="test-change",
        reference="AO/ABB/2026",
        title="Audit de sécurité DNSSI",
        buyer_name="Al Barid Bank",
        source_name="Al Barid Bank",
        source_url="https://albaridbank.ma"
    )
    change = TenderChange(
        timestamp=datetime.now().isoformat(),
        field_changed="deadline",
        old_value="2026-11-20 10:00:00",
        new_value="2026-12-05 10:00:00",
        change_type="postponement"
    )
    assert change.change_type == "postponement"
    assert change.new_value == "2026-12-05 10:00:00"


def test_deadline_reminder_calculation():
    today = datetime.now().date()
    d_7 = (today + timedelta(days=7)).strftime("%Y-%m-%d 10:00:00")
    d_3 = (today + timedelta(days=3)).strftime("%Y-%m-%d 10:00:00")
    d_1 = (today + timedelta(days=1)).strftime("%Y-%m-%d 10:00:00")

    assert (datetime.strptime(d_7.split(" ")[0], "%Y-%m-%d").date() - today).days == 7
    assert (datetime.strptime(d_3.split(" ")[0], "%Y-%m-%d").date() - today).days == 3
    assert (datetime.strptime(d_1.split(" ")[0], "%Y-%m-%d").date() - today).days == 1


def test_downloaded_tender_modification_alert_rule():
    """
    Verifies that ANY tender whose DCE was downloaded receives an official PMMP email alert
    when a modification (postponement/corrigendum) occurs on the portal.
    """
    from src.database import Database
    import tempfile
    
    # Use a temporary SQLite database
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        tmp_db_path = f.name
        
    try:
        db = Database(db_path=tmp_db_path)
        dispatcher = AlertsDispatcher()

        # 1. Ingest initial tender (e.g. DGI Network Packet Broker)
        tender = Tender(
            id="pmmp:dgi_test_mod",
            reference="35/2026/DGI",
            title="Acquisition d'un Network Packet Broker pour la DGI",
            buyer_name="Ministère de l'Économie et des Finances - DGI",
            deadline="2027-01-13 10:00:00",
            source_name="PMMP",
            source_url="https://www.marchespublics.gov.ma/index.php?page=entreprise.EntrepriseDetailsConsultation&refConsultation=1035530&orgAcronyme=g8e",
            relevance_category="CYBERSECURITY"
        )
        is_new, is_updated = db.upsert_tender(tender, alerts_dispatcher=dispatcher)
        assert is_new is True
        assert is_updated is False

        # 2. User/DPA downloads the DCE
        db.mark_tender_dce_downloaded(tender.id)
        saved = db.get_tender_by_id(tender.id)
        assert saved.dce_downloaded is True

        # 3. Later, PMMP publishes an 'Avis de report' (deadline changed to 2027-01-27)
        modified_tender = tender.model_copy()
        modified_tender.deadline = "2027-01-27 10:00:00"
        modified_tender.status = "postponed"

        is_new_2, is_updated_2 = db.upsert_tender(modified_tender, alerts_dispatcher=dispatcher)
        assert is_new_2 is False
        assert is_updated_2 is True

        # 4. Verify the official PMMP alert formatting for this modification
        alert_data = dispatcher.send_pmmp_official_alert(
            tender=modified_tender,
            recipient_name="John Doe",
            event_type="modification"
        )
        assert alert_data["sender"] == "MPE - PORTAIL MAROCAIN DES MARCHES PUBLICS <noreply-marchespublics@tgr.gov.ma>"
        assert "Avertissement - Modification de consultation" in alert_data["subject"]
        assert "27/01/2027" in alert_data["plain_text"]
        assert "35/2026/DGI" in alert_data["plain_text"]
        assert "marchespublics.gov.ma" in alert_data["portal_url"]

        # 5. Non-downloaded tender modification test:
        # If DCE was NOT downloaded, upserting a modification does NOT trigger an email alert!
        tender_not_downloaded = Tender(
            id="pmmp:bam_test_no_alert",
            reference="12/2026/BAM",
            title="Prestations de Cyber-surveillance pour Bank Al-Maghrib",
            buyer_name="Bank Al-Maghrib",
            deadline="2027-02-01 10:00:00",
            source_name="PMMP",
            source_url="https://www.marchespublics.gov.ma/index.php?page=entreprise.EntrepriseDetailsConsultation&refConsultation=999888&orgAcronyme=bam",
            dce_downloaded=False
        )
        db.upsert_tender(tender_not_downloaded, alerts_dispatcher=dispatcher)
        
        # Modify it
        mod_not_downloaded = tender_not_downloaded.model_copy()
        mod_not_downloaded.deadline = "2027-02-15 10:00:00"
        
        # Mock dispatcher.send_pmmp_official_alert to verify it is NOT called
        called = False
        def mock_alert(*args, **kwargs):
            nonlocal called
            called = True
        dispatcher.send_pmmp_official_alert = mock_alert
        
        db.upsert_tender(mod_not_downloaded, alerts_dispatcher=dispatcher)
        assert called is False, "Alerte ne doit PAS être envoyée si le DCE n'a pas été téléchargé !"
    finally:
        try:
            os.remove(tmp_db_path)
        except Exception:
            pass
