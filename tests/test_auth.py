"""
Unit and Integration Tests for Team Authentication and @dpg-cyber.com User Management
"""
import pytest
from fastapi.testclient import TestClient
from src.server import app, db


@pytest.fixture
def client():
    return TestClient(app)


def test_login_page_renders_dpg_branding(client):
    response = client.get("/login")
    assert response.status_code == 200
    assert "@dpg-cyber.com" in response.text
    assert "CyberRFP Maroc" in response.text
    assert "DataProtech" in response.text


def test_registration_rejects_external_email_domain(client):
    # Attempt registration with non-dpg-cyber.com email
    payload = {
        "email": "intruder@gmail.com",
        "full_name": "External User",
        "role": "Consultant Cybersécurité",
        "password": "Password123!",
        "send_password_by_email": False
    }
    response = client.post("/api/auth/register", json=payload)
    assert response.status_code == 400
    assert "dpg-cyber.com" in response.json()["detail"].lower()


def test_registration_and_login_flow_dpg_team(client):
    import secrets
    email = f"consultant_{secrets.token_hex(4)}@dpg-cyber.com"
    full_name = "Karim Alami"
    password = "TestPassword2026!"

    # 1. Register new DPG collaborator
    reg_payload = {
        "email": email,
        "full_name": full_name,
        "role": "Ingénieur Réseau, Firewall & Cloud",
        "password": password,
        "send_password_by_email": False
    }
    r_reg = client.post("/api/auth/register", json=reg_payload)
    assert r_reg.status_code == 200
    reg_data = r_reg.json()
    assert reg_data["status"] == "success"
    assert reg_data["user"]["email"] == email

    # 2. Login with valid credentials
    login_payload = {
        "email": email,
        "password": password,
        "remember_me": True
    }
    r_login = client.post("/api/auth/login", json=login_payload)
    assert r_login.status_code == 200
    assert "dpa_session" in r_login.cookies
    session_cookie = r_login.cookies["dpa_session"]

    # 3. Access /api/auth/me using the session cookie
    r_me = client.get("/api/auth/me", cookies={"dpa_session": session_cookie})
    assert r_me.status_code == 200
    me_data = r_me.json()
    assert me_data["email"] == email
    assert me_data["full_name"] == full_name

    # 4. Access dashboard / using the session cookie (should not redirect)
    r_dash = client.get("/", cookies={"dpa_session": session_cookie})
    assert r_dash.status_code == 200
    assert "CyberRFP" in r_dash.text

    # 5. Logout
    r_logout = client.get("/logout", cookies={"dpa_session": session_cookie}, follow_redirects=False)
    assert r_logout.status_code == 303
    assert r_logout.headers["location"] == "/login"


def test_login_invalid_password_rejected(client):
    login_payload = {
        "email": "john.doe@dpg-cyber.com",
        "password": "WrongPassword123!",
        "remember_me": False
    }
    r_login = client.post("/api/auth/login", json=login_payload)
    assert r_login.status_code == 400


def test_password_reset_flow(client):
    email = "john.doe@dpg-cyber.com"
    
    # 1. Request reset link
    r_forgot = client.post("/api/auth/forgot-password", json={"email": email})
    assert r_forgot.status_code == 200
    forgot_data = r_forgot.json()
    assert forgot_data["status"] == "success"
    
    # Get the token generated in the DB
    user = db.get_user_by_email(email)
    assert user is not None
    # Read the reset token from database
    with db.get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT reset_token FROM users WHERE email = ?", (email,))
        token = cursor.fetchone()[0]
    
    assert token is not None

    # 2. Reset password using the token
    new_password = "NewStrongPassword2026!"
    r_reset = client.post("/api/auth/reset-password", json={
        "token": token,
        "new_password": new_password
    })
    assert r_reset.status_code == 200

    # 3. Login with the new password
    r_login_new = client.post("/api/auth/login", json={
        "email": email,
        "password": new_password,
        "remember_me": True
    })
    assert r_login_new.status_code == 200

    # Restore default password for other tests
    r_restore = client.post("/api/auth/forgot-password", json={"email": email})
    with db.get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT reset_token FROM users WHERE email = ?", (email,))
        tok = cursor.fetchone()[0]
    client.post("/api/auth/reset-password", json={"token": tok, "new_password": "cyberrfp2026"})


def test_first_login_mandatory_password_change_flow(client):
    """
    Validates that:
    1. A team member registered with generated password gets must_change_password=1
    2. Attempting to log in returns status='must_change_password' (no active session yet)
    3. User must call /api/auth/change-initial-password to set their permanent password
    4. Upon setting new password, must_change_password becomes 0 and a session is granted
    5. Single-name email format (e.g. achraf@dpg-cyber.com) works perfectly
    """
    import secrets
    username = f"expert{secrets.token_hex(3)}"
    email = f"{username}@dpg-cyber.com"
    full_name = "Achraf"

    # 1. Register with send_password_by_email=True (generates temporary password)
    r_reg = client.post("/api/auth/register", json={
        "email": email,
        "full_name": full_name,
        "role": "Consultant Cybersécurité",
        "send_password_by_email": True
    })
    assert r_reg.status_code == 200
    reg_data = r_reg.json()
    temp_password = reg_data.get("temp_password_preview")
    assert temp_password is not None
    assert temp_password.startswith("DPG-2026-")

    # 2. Verify must_change_password flag in DB
    db_user = db.get_user_by_email(email)
    assert db_user["must_change_password"] == 1

    # 3. First login attempt with temporary password
    r_login = client.post("/api/auth/login", json={
        "email": email,
        "password": temp_password,
        "remember_me": True
    })
    assert r_login.status_code == 200
    login_data = r_login.json()
    assert login_data["status"] == "must_change_password"
    assert "dpa_session" not in r_login.cookies

    # 4. Attempt to change password with too short password
    r_bad = client.post("/api/auth/change-initial-password", json={
        "email": email,
        "temp_password": temp_password,
        "new_password": "short"
    })
    assert r_bad.status_code == 400

    # 5. Attempt to use identical password
    r_same = client.post("/api/auth/change-initial-password", json={
        "email": email,
        "temp_password": temp_password,
        "new_password": temp_password
    })
    assert r_same.status_code == 400

    # 6. Set real personal password
    personal_password = "AchrafPersonalPassword2026!"
    r_change = client.post("/api/auth/change-initial-password", json={
        "email": email,
        "temp_password": temp_password,
        "new_password": personal_password
    })
    assert r_change.status_code == 200
    change_data = r_change.json()
    assert change_data["status"] == "success"
    assert "dpa_session" in r_change.cookies
    active_cookie = r_change.cookies["dpa_session"]

    # 7. Check that must_change_password is now 0
    updated_user = db.get_user_by_email(email)
    assert updated_user["must_change_password"] == 0

    # 8. User can now access dashboard with their active session
    r_dash = client.get("/", cookies={"dpa_session": active_cookie})
    assert r_dash.status_code == 200

    # 9. Next time, regular login directly succeeds
    r_next_login = client.post("/api/auth/login", json={
        "email": email,
        "password": personal_password,
        "remember_me": True
    })
    assert r_next_login.status_code == 200
    assert r_next_login.json()["status"] == "success"
    assert "dpa_session" in r_next_login.cookies

