"""
Tests for FastAPI Server, Database Deduplication, and Endpoints
"""
import sys
import os
import pytest
from datetime import datetime
from fastapi.testclient import TestClient

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.database import Database
from src.server import app
from src.models import Tender, DocumentItem


@pytest.fixture
def test_db(tmp_path):
    db_file = str(tmp_path / "test_cyberrfp.db")
    db = Database(db_path=db_file)
    return db


def test_database_upsert_and_deduplication(test_db):
    t1 = Tender(
        id="pmmp:12345",
        reference="AO/01/2026",
        title="Mise en place d'un SOC et SIEM",
        buyer_name="Office de la Formation Professionnelle et de la Promotion du Travail (OFPPT)",
        buyer_normalized="OFPPT",
        is_priority_buyer=True,
        priority_badge="OFPPT (Prioritaire)",
        procedure_type="AOO",
        deadline="2027-01-15 10:00:00",
        estimated_budget=2500000.0,
        source_name="PMMP",
        source_url="https://marchespublics.gov.ma/detail1",
        relevance_category="CYBERSECURITY",
        relevance_score=85,
        sub_category="SOC & Supervision SIEM",
        document_links=[DocumentItem(title="DCE", url="https://marchespublics.gov.ma/dce1")]
    )
    is_new, is_updated = test_db.upsert_tender(t1)
    assert is_new is True
    assert is_updated is False

    # Same tender found on second source (OFPPT backup site)
    t2 = Tender(
        id="ofppt:99999",
        reference="AO/01/2026",
        title="Mise en place d'un SOC et SIEM",
        buyer_name="OFPPT Direction Générale",
        buyer_normalized="OFPPT",
        is_priority_buyer=True,
        priority_badge="OFPPT (Prioritaire)",
        procedure_type="AOO",
        deadline="2027-01-20 10:00:00",  # Postponed deadline!
        estimated_budget=2500000.0,
        source_name="OFPPT",
        source_url="https://ofppt.ma/tender1",
        relevance_category="CYBERSECURITY",
        relevance_score=85,
        document_links=[DocumentItem(title="Reglement", url="https://ofppt.ma/rc.pdf")]
    )
    is_new, is_updated = test_db.upsert_tender(t2)
    assert is_new is False
    assert is_updated is True

    # Retrieve and verify deduplicated tender has postponed deadline and merged documents
    fetched = test_db.get_tender_by_id("pmmp:12345")
    assert fetched is not None
    assert fetched.deadline == "2027-01-20 10:00:00"
    assert fetched.status == "postponed"
    assert len(fetched.document_links) == 2
    assert len(fetched.history) >= 2
    assert any(h.change_type == "postponement" for h in fetched.history)


def test_api_endpoints_auth_and_filtering():
    client = TestClient(app)
    auth = ("admin", "cyberrfp2026")

    # 1. Unauthenticated request should return 401
    r_unauth = client.get("/api/tenders")
    assert r_unauth.status_code == 401

    # 2. Authenticated request
    r_auth = client.get("/api/tenders", auth=auth)
    assert r_auth.status_code == 200
    data = r_auth.json()
    assert "tenders" in data
    assert "total" in data

    # 3. HTML Dashboard access
    r_dash = client.get("/", auth=auth)
    assert r_dash.status_code == 200
    assert "CyberRFP" in r_dash.text
    assert "Maroc" in r_dash.text

    # 4. Admin Scrapers endpoint
    r_scrapers = client.get("/api/admin/scrapers", auth=auth)
    assert r_scrapers.status_code == 200

    # 5. Admin Watchlist endpoint
    r_wl = client.get("/api/admin/watchlist", auth=auth)
    assert r_wl.status_code == 200
    wl_items = r_wl.json()
    assert len(wl_items) > 0
    assert any(b["name"] == "OFPPT" for b in wl_items)
    assert any(b["name"] == "Al Barid Bank" for b in wl_items)
    assert any(b["name"] == "SOREC" for b in wl_items)


def test_download_tender_dce_endpoint():
    client = TestClient(app)
    auth = ("admin", "cyberrfp2026")

    # Get one existing tender from DB
    r_tenders = client.get("/api/tenders?limit=1", auth=auth)
    assert r_tenders.status_code == 200
    tenders = r_tenders.json().get("tenders", [])
    if len(tenders) > 0:
        t_id = tenders[0]["id"]
        r_dl = client.get(f"/api/tenders/{t_id}/download-dce", auth=auth)
        assert r_dl.status_code == 200
        assert r_dl.headers.get("content-type") == "application/zip"
        assert "DCE_" in r_dl.headers.get("content-disposition", "")
        assert len(r_dl.content) > 1000


def test_pmmp_official_alert_endpoint():
    client = TestClient(app)
    auth = ("admin", "cyberrfp2026")

    # Get one existing tender
    r_tenders = client.get("/api/tenders?limit=1", auth=auth)
    assert r_tenders.status_code == 200
    tenders = r_tenders.json().get("tenders", [])
    if len(tenders) > 0:
        t_id = tenders[0]["id"]
        r_alert = client.post(f"/api/tenders/{t_id}/send-alert", auth=auth)
        assert r_alert.status_code == 200
        data = r_alert.json()
        assert data["sender"] == "MPE - PORTAIL MAROCAIN DES MARCHES PUBLICS <noreply-marchespublics@tgr.gov.ma>"
        assert "Avertissement" in data["subject"]
        assert "Bonjour" in data["plain_text"]
        assert "Objet de la consultation :" in data["plain_text"]
        assert "Référence consultation :" in data["plain_text"]
        assert "DataProtech Group" in data["html"]
        assert "DPA" in data["html"]


def test_tenders_ranked_by_day_publication_date():
    client = TestClient(app)
    auth = ("admin", "cyberrfp2026")

    # Get tenders sorted by publication date descending
    r_tenders = client.get("/api/tenders?source=PMMP&sort_by=publication_desc&limit=20", auth=auth)
    assert r_tenders.status_code == 200
    tenders = r_tenders.json().get("tenders", [])
    assert len(tenders) > 0

    # Verify all tenders are from PMMP
    for t in tenders:
        assert t["source_name"] == "PMMP"
        assert "marchespublics.gov.ma" in t["source_url"]

    # Verify descending publication order
    pub_dates = [t["publication_date"] for t in tenders if t.get("publication_date")]
    for i in range(len(pub_dates) - 1):
        assert pub_dates[i] >= pub_dates[i+1]


def test_tenders_ranked_by_response_deadline():
    client = TestClient(app)
    auth = ("admin", "cyberrfp2026")

    # Get tenders sorted by response deadline ascending (earliest / most urgent deadline first)
    r_tenders = client.get("/api/tenders?sort_by=deadline_asc&limit=30", auth=auth)
    assert r_tenders.status_code == 200
    tenders = r_tenders.json().get("tenders", [])
    assert len(tenders) > 0

    # Verify ascending deadline order
    deadlines = [t["deadline"] for t in tenders if t.get("deadline")]
    assert len(deadlines) > 0
    for i in range(len(deadlines) - 1):
        assert deadlines[i] <= deadlines[i+1]


def test_submission_folder_endpoint():
    client = TestClient(app)
    auth = ("admin", "cyberrfp2026")

    r_tenders = client.get("/api/tenders?limit=5", auth=auth)
    assert r_tenders.status_code == 200
    tenders = r_tenders.json().get("tenders", [])
    assert len(tenders) > 0

    t_id = tenders[0]["id"]
    r_sub = client.get(f"/api/tenders/{t_id}/submission-folder", auth=auth)
    assert r_sub.status_code == 200
    data = r_sub.json()

    assert data["tender_id"] == t_id
    assert "administrative_items" in data
    assert len(data["administrative_items"]) == 7
    # Verify corporate credentials
    signataire_item = next(item for item in data["administrative_items"] if item["num"] == 2)
    assert "John Doe" in signataire_item["requirement"]
    ice_item = next(item for item in data["administrative_items"] if item["num"] == 4)
    assert "003102490000030" in ice_item["requirement"]

    # Verify technical documents and profiles grid
    assert "technical_documents" in data
    assert len(data["technical_documents"]) == 7
    assert "technical_profiles" in data
    assert len(data["technical_profiles"]) > 0
    p1 = data["technical_profiles"][0]
    for key in ["num", "profile_title", "min_experience", "skills", "certifications", "lot", "dpa_status"]:
        assert key in p1

    # Verify financial folder
    assert "financial_folder" in data
    assert "budget_ttc_mad" in data["financial_folder"]
    assert "budget_ht_mad" in data["financial_folder"]
    assert "tva_mad" in data["financial_folder"]
    assert len(data["financial_folder"]["documents"]) == 3


def test_notifications_api_endpoints():
    client = TestClient(app)
    auth = ("admin", "cyberrfp2026")

    # 1. Test latest notifications
    r_notif = client.get("/api/notifications/latest?limit=5", auth=auth)
    assert r_notif.status_code == 200
    data = r_notif.json()
    assert data["status"] == "success"
    assert "server_time" in data
    assert "count" in data
    assert isinstance(data["tenders"], list)
    assert len(data["tenders"]) > 0

    # 2. Test test-sample notification endpoint
    r_sample = client.get("/api/notifications/test-sample", auth=auth)
    assert r_sample.status_code == 200
    sample = r_sample.json()
    assert "reference" in sample
    assert "title" in sample
    assert "buyer_name" in sample
    assert sample.get("is_test") is True


def test_expired_tender_filtering_by_default():
    """
    Verifies that tenders with past deadlines (like yesterday) are filtered out by default,
    and only returned when include_expired=True is explicitly passed.
    """
    client = TestClient(app)
    auth = ("admin", "cyberrfp2026")

    # 1. Default request should NOT include any tender where deadline < now
    res_default = client.get("/api/tenders?limit=200", auth=auth)
    assert res_default.status_code == 200
    tenders_active = res_default.json()["tenders"]

    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    for t in tenders_active:
        if t.get("deadline"):
            assert t["deadline"] >= now_str, f"Tender {t['reference']} has past deadline {t['deadline']}"

    # 2. Request with include_expired=True should return past tenders as well
    res_all = client.get("/api/tenders?limit=200&include_expired=true", auth=auth)
    assert res_all.status_code == 200
    tenders_all = res_all.json()["tenders"]
    assert len(tenders_all) >= len(tenders_active)


def test_network_info_and_mobile_pwa_endpoints():
    """Verifies LAN network discovery for iPhone access and PWA manifest."""
    client = TestClient(app)
    auth = ("admin", "cyberrfp2026")

    # 1. PWA Manifest
    res_manifest = client.get("/manifest.json")
    assert res_manifest.status_code == 200
    manifest = res_manifest.json()
    assert manifest["short_name"] in ["CyberRFP", "CyberRFP DPA"]
    assert manifest["display"] == "standalone"
    assert len(manifest["icons"]) >= 2

    # 2. Network info for iPhone
    res_net = client.get("/api/system/network-info", auth=auth)
    assert res_net.status_code == 200
    net_data = res_net.json()
    assert net_data["status"] == "success"
    assert "lan_ip" in net_data
    assert "mobile_url" in net_data
    assert "port" in net_data


def test_tender_tracking_and_test_email_endpoints():
    """Verifies marking an RFP as tracked and dispatching test email alerts."""
    client = TestClient(app)
    auth = ("admin", "cyberrfp2026")

    # Pick an existing tender or seed a test one
    from src.database import Database
    from src.models import Tender
    db_inst = Database()
    tenders = db_inst.get_tenders(category="CYBERSECURITY", limit=1)
    if not tenders:
        tenders = db_inst.get_tenders(limit=1)
    if not tenders:
        sample = Tender(
            id="test:active-rfp-sample",
            reference="32/2026/ONHYM",
            title="Audit de cybersécurité et Pentest",
            buyer_name="ONHYM",
            buyer_normalized="onhym",
            category="Services",
            sub_category="Cybersécurité",
            relevance_category="CYBERSECURITY",
            relevance_score=95,
            source_name="PMMP",
            source_url="https://www.marchespublics.gov.ma",
            publication_date="2026-11-25",
            deadline="2026-12-15 10:00:00"
        )
        db_inst.upsert_tender(sample)
        test_id = sample.id
        test_ref = sample.reference
    else:
        test_id = tenders[0].id
        test_ref = tenders[0].reference

    # 1. Track a tender
    res_track = client.post(f"/api/tenders/{test_id}/track?track=true", auth=auth)
    assert res_track.status_code == 200
    track_data = res_track.json()
    assert track_data["tracked"] is True
    assert track_data["tender_id"] == test_id

    # Untrack
    res_untrack = client.post(f"/api/tenders/{test_id}/track?track=false", auth=auth)
    assert res_untrack.status_code == 200
    assert res_untrack.json()["tracked"] is False

    # 2. Test email alert endpoint
    res_email = client.post(
        f"/api/admin/alerts/test-email?recipient=john.doe@dpg-cyber.com&tender_id={test_id}",
        auth=auth
    )
    assert res_email.status_code == 200
    email_data = res_email.json()
    assert email_data["status"] in ["success", "queued"]
    assert "john.doe@dpg-cyber.com" in email_data["recipient"]
    assert test_ref in email_data["tender_reference"]


def test_notifications_only_tracked_filter():
    """Verifies that notifications with only_tracked=True only return tracked RFPs."""
    client = TestClient(app)
    auth = ("admin", "cyberrfp2026")

    from src.database import Database
    from src.models import Tender
    db_inst = Database()
    tenders = db_inst.get_tenders(category="CYBERSECURITY", limit=1)
    if not tenders:
        tenders = db_inst.get_tenders(limit=1)
    test_id = tenders[0].id if tenders else "test:sample-tracked"

    # 1. Track a specific RFP
    client.post(f"/api/tenders/{test_id}/track?track=true", auth=auth)

    # 2. Query notifications with only_tracked=True and tracked_ids
    res = client.get(f"/api/notifications/latest?only_tracked=true&tracked_ids={test_id}", auth=auth)
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "success"
    for t in data["tenders"]:
        assert t["id"] == test_id or t.get("alert_on_modification") == 1 or t.get("dce_downloaded") == 1




