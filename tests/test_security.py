"""
Security Regression Tests for CyberRFP Maroc
Verifies patches for VULN-01 through VULN-09:
- VULN-01: Password reset token concealment
- VULN-02: User registration password concealment in production
- VULN-03: SQL wildcard injection immunity
- VULN-04: Rate limiter protection
- VULN-05: SSRF protection on generic connector endpoints
- VULN-06: HTML injection sanitization in alert dispatcher
- VULN-08: HTTP Security headers (X-Frame-Options, CSP, nosniff)
- VULN-09: Gemini API key injection sanitization
"""
import os
import sys
import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from starlette.testclient import TestClient

from src.server import app, auth_rate_limiter, InMemoryRateLimiter
from src.database import Database
from src.connectors.generic import validate_safe_url
from src.alerts.dispatcher import AlertsDispatcher
from src.models import Tender


@pytest.fixture
def client():
    return TestClient(app)


def test_vuln01_forgot_password_never_leaks_reset_token(client):
    """VULN-01: Verifies /api/auth/forgot-password does NOT expose reset_link_preview."""
    resp = client.post("/api/auth/forgot-password", json={"email": "sec.audit@dpg-cyber.com"})
    assert resp.status_code == 200
    data = resp.json()
    assert data.get("status") == "success"
    # reset_link_preview must strictly be None in responses
    assert data.get("reset_link_preview") is None
    assert "token" not in str(data)


def test_vuln02_registration_production_password_concealment(client, monkeypatch):
    """VULN-02: Verifies temporary password preview is suppressed outside test environments."""
    # Simulate production environment without pytest marker
    monkeypatch.delenv("PYTEST_CURRENT_TEST", raising=False)
    
    email = f"prod.user.{os.urandom(4).hex()}@dpg-cyber.com"
    resp = client.post("/api/auth/register", json={
        "email": email,
        "full_name": "Prod Security User",
        "role": "Consultant SSI",
        "send_password_by_email": True
    })
    assert resp.status_code == 200
    data = resp.json()
    assert data.get("temp_password_preview") is None


def test_vuln03_database_wildcard_sanitization():
    """VULN-03: Verifies wildcard characters cannot match or bypass user auth."""
    db = Database()
    # Try logging in with % or _ wildcards
    user = db.authenticate_user("%", "any_password")
    assert user is None
    user2 = db.authenticate_user("_", "any_password")
    assert user2 is None
    user3 = db.authenticate_user("admin%@dpg-cyber.com", "any_password")
    assert user3 is None


def test_vuln04_rate_limiter_blocks_excessive_requests():
    """VULN-04: Verifies sliding window rate limiter prevents brute-force attempts."""
    limiter = InMemoryRateLimiter(max_requests=3, window_seconds=10)
    key = "test_ip_192_168_1_50"
    
    assert limiter.is_allowed(key) is True
    assert limiter.is_allowed(key) is True
    assert limiter.is_allowed(key) is True
    # 4th request must be rejected
    assert limiter.is_allowed(key) is False


def test_vuln05_ssrf_validator_blocks_internal_ranges():
    """VULN-05: Verifies validate_safe_url rejects loopback, RFC 1918, and metadata endpoints."""
    # Loopback
    with pytest.raises(ValueError, match="SSRF"):
        validate_safe_url("http://127.0.0.1:8080/admin")
    with pytest.raises(ValueError, match="SSRF"):
        validate_safe_url("http://localhost:8000/api")

    # AWS / Cloud Metadata endpoint
    with pytest.raises(ValueError, match="SSRF"):
        validate_safe_url("http://169.254.169.254/latest/meta-data/")

    # Private network
    with pytest.raises(ValueError, match="SSRF"):
        validate_safe_url("http://192.168.1.1/router")
    with pytest.raises(ValueError, match="SSRF"):
        validate_safe_url("http://10.0.0.1/internal")

    # Disallowed scheme
    with pytest.raises(ValueError, match="Protocole non autorisé"):
        validate_safe_url("file:///etc/passwd")


def test_vuln05_generic_connector_api_blocks_ssrf(client):
    """VULN-05: Verifies POST /api/admin/generic-connectors rejects SSRF payloads."""
    auth = ("admin", "cyberrfp2026")
    resp = client.post(
        "/api/admin/generic-connectors",
        json={
            "id": "malicious_connector",
            "name": "Internal Probe",
            "listing_url": "http://127.0.0.1:8000/internal"
        },
        auth=auth
    )
    assert resp.status_code == 400
    assert "SSRF protection" in resp.json().get("detail", "")


def test_vuln06_email_html_injection_escaping():
    """VULN-06: Verifies user-controllable input in emails is escaped against HTML injection."""
    dispatcher = AlertsDispatcher()
    
    # We check the generated content directly by calling format_pmmp_official_email
    tender = Tender(
        id="sample:injection",
        reference="REF<script>123",
        title="Title with <script>alert(1)</script> & injection",
        buyer_name="Buyer <svg/onload=alert(1)>",
        source_name="PMMP <img src=x>",
        source_url="https://marchespublics.gov.ma?param=<test>"
    )
    subject, html_body, plain_text = dispatcher.format_pmmp_official_email(
        tender=tender,
        recipient_name="<img src=x onerror=alert(1)>"
    )
    
    assert "<script>" not in html_body
    assert "<svg" not in html_body
    assert "&lt;script&gt;" in html_body
    assert "&lt;svg/onload=alert(1)&gt;" in html_body


def test_vuln08_security_headers_present(client):
    """VULN-08: Verifies HTTP security headers (OWASP Top 10) are returned."""
    resp = client.get("/login")
    assert resp.headers.get("X-Frame-Options") == "SAMEORIGIN"
    assert resp.headers.get("X-Content-Type-Options") == "nosniff"
    assert resp.headers.get("X-XSS-Protection") == "1; mode=block"
    assert resp.headers.get("Referrer-Policy") == "strict-origin-when-cross-origin"
    assert "frame-ancestors 'self'" in resp.headers.get("Content-Security-Policy", "")


def test_vuln09_gemini_key_rejects_newlines_and_injection(client):
    """VULN-09: Verifies /api/admin/gemini-key rejects keys containing newlines or illegal chars."""
    auth = ("admin", "cyberrfp2026")
    
    # Injection attempt with newline to pollute .env
    bad_key = "AIzaSyValidPart\nADMIN_PASSWORD=hacked"
    resp = client.post("/api/admin/gemini-key", json={"api_key": bad_key}, auth=auth)
    assert resp.status_code == 400
    assert "Format de clé invalide" in resp.json().get("detail", "")

    # Injection with shell characters
    bad_key2 = "AIzaSyValidPart; rm -rf /"
    resp2 = client.post("/api/admin/gemini-key", json={"api_key": bad_key2}, auth=auth)
    assert resp2.status_code == 400
