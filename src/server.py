"""
FastAPI Server & REST API for CyberRFP Maroc
Serves the responsive multi-lingual dashboard and JSON endpoints.
Includes HTTP Basic Auth, pipeline management, scraper orchestration, and alerts configuration.
"""
import os
import sys
import re
import logging
import secrets
import html
import time
from urllib.parse import urlparse
from collections import defaultdict
from datetime import datetime, timedelta
from contextlib import asynccontextmanager
from typing import List, Optional, Dict, Any
from fastapi import FastAPI, Depends, HTTPException, status, Request, Response, Query, BackgroundTasks
from fastapi.responses import HTMLResponse, JSONResponse, FileResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from pydantic import BaseModel

from src.database import Database
from src.models import (
    Tender, ScraperHealth, WatchlistBuyer,
    UserRegister, UserLogin, PasswordResetRequest, PasswordResetSubmit,
    FirstLoginPasswordChange
)
from src.classifier.engine import ClassifierEngine
from src.dce_downloader import DCEDownloader
from src.connectors.pmmp import PMMPConnector
from src.connectors.albaridbank import AlBaridBankConnector
from src.connectors.ofppt import OFPPTConnector
from src.connectors.sorec import SORECConnector
from src.connectors.generic import GenericConfigurableConnector
from src.connectors.press_journal import PressJournalConnector
from src.alerts.scheduler import RFPTaskScheduler
from src.alerts.dispatcher import AlertsDispatcher
from src.tender_requirements import get_submission_folder_data

logger = logging.getLogger("cyberrfp.server")
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

if getattr(sys, "frozen", False):
    BUNDLE_DIR = sys._MEIPASS
    STATIC_DIR = os.path.join(BUNDLE_DIR, "src", "static")
    TEMPLATES_DIR = os.path.join(BUNDLE_DIR, "src", "templates")
else:
    STATIC_DIR = os.path.join(BASE_DIR, "static")
    TEMPLATES_DIR = os.path.join(BASE_DIR, "templates")

templates = Jinja2Templates(directory=TEMPLATES_DIR)
security = HTTPBasic(auto_error=False)
db = Database()
classifier = ClassifierEngine()
dce_downloader = DCEDownloader()
alerts_dispatcher = AlertsDispatcher(db.get_alerts_config())

# Connectors registry
connectors: Dict[str, Any] = {
    "pmmp": PMMPConnector(fetch_details=True),
    "albaridbank": AlBaridBankConnector(fetch_details=True),
    "ofppt": OFPPTConnector(),
    "sorec": SORECConnector(),
    "press_journal": PressJournalConnector(),
}

# Dynamically add saved generic connectors
for gen_cfg in db.get_generic_connectors():
    if gen_cfg.get("is_active", 1):
        connectors[gen_cfg["id"]] = GenericConfigurableConnector(gen_cfg)

scheduler: Optional[RFPTaskScheduler] = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    global scheduler
    is_test_env = os.environ.get("PYTEST_CURRENT_TEST") is not None
    # Purge legacy synthetic blog-URL press rows & normalize PMMP labels
    try:
        db.cleanup_polluted_tenders(classifier=classifier)
    except Exception as e:
        logger.warning(f"Startup DB cleanup warning: {e}")

    scheduler = RFPTaskScheduler(db=db, connectors=connectors, classifier=classifier)
    scheduler.start()

    # Run immediate background sync in live mode (avoid stalling pytest startup)
    if not is_test_env:
        import threading
        threading.Thread(target=scheduler.job_sync_all_sources, daemon=True).start()

    yield
    if scheduler:
        scheduler.stop()

# Initialize App & Dependencies
app = FastAPI(title="CyberRFP Maroc API", version="1.0.0", lifespan=lifespan)
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

# ==================== SECURITY HEADERS & RATE LIMITING ====================

class InMemoryRateLimiter:
    """Sliding-window in-memory rate limiter for brute-force prevention."""
    def __init__(self, max_requests: int = 10, window_seconds: int = 60):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.requests = defaultdict(list)

    def is_allowed(self, key: str) -> bool:
        now = time.time()
        # Bound memory growth across many unique keys
        if len(self.requests) > 1000:
            stale = [k for k, ts in self.requests.items() if not ts or now - ts[-1] >= self.window_seconds]
            for k in stale:
                del self.requests[k]
        self.requests[key] = [t for t in self.requests[key] if now - t < self.window_seconds]
        if len(self.requests[key]) >= self.max_requests:
            return False
        self.requests[key].append(now)
        return True

def _safe_base_url(request: Request) -> str:
    """Constructs a canonical origin URL guarding against Host Header Injection."""
    raw = str(request.base_url).rstrip("/")
    parsed = urlparse(raw)
    if parsed.scheme in ("http", "https") and parsed.netloc and re.match(r"^[A-Za-z0-9\.\-:\[\]]+$", parsed.netloc):
        return f"{parsed.scheme}://{parsed.netloc}/"
    return "http://localhost:8000/"

auth_rate_limiter = InMemoryRateLimiter(max_requests=10, window_seconds=60)

@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    """Enforces essential HTTP security headers (OWASP Top 10 / Clickjacking / MIME-sniffing)."""
    response = await call_next(request)
    response.headers["X-Frame-Options"] = "SAMEORIGIN"
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"
    response.headers["Content-Security-Policy"] = "default-src 'self' 'unsafe-inline' 'unsafe-eval' https: data: blob:; frame-ancestors 'self';"
    return response


def authenticate(
    request: Request,
    credentials: Optional[HTTPBasicCredentials] = Depends(security)
) -> str:
    """
    Verifies authentication via:
    1. HTTP Basic Auth (for automated test suites and API clients)
    2. Cookie-based Session 'dpa_session' (for web browser users)
    If unauthenticated and visiting a web page (GET /), redirects to /login.
    """
    # 1. HTTP Basic Auth check
    if credentials:
        expected_user = os.environ.get("ADMIN_USER", "admin")
        expected_password = os.environ.get("ADMIN_PASSWORD", "cyberrfp2026")
        if secrets.compare_digest(credentials.username, expected_user) and secrets.compare_digest(credentials.password, expected_password):
            return credentials.username
        
        # Check against database users
        db_user = db.authenticate_user(credentials.username, credentials.password)
        if db_user:
            return db_user.get("full_name") or db_user.get("email")

    # 2. Cookie Session check
    session_token = request.cookies.get("dpa_session")
    if session_token:
        user = db.get_user_by_session(session_token)
        if user:
            return user.get("full_name") or user.get("email")

    # 3. Unauthenticated handling:
    # If browser requesting HTML page (e.g. GET /), redirect to /login
    accept = request.headers.get("accept", "")
    if request.url.path == "/" and ("text/html" in accept or "*/*" in accept) and not credentials:
        raise HTTPException(
            status_code=status.HTTP_307_TEMPORARY_REDIRECT,
            headers={"Location": "/login"}
        )

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Identifiants requis pour CyberRFP Maroc",
        headers={"WWW-Authenticate": "Basic"},
    )


# ==================== AUTHENTICATION & TEAM ACCOUNTS ====================

@app.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    """Renders the professional login and registration page for @dpg-cyber.com."""
    session_token = request.cookies.get("dpa_session")
    if session_token and db.get_user_by_session(session_token):
        return RedirectResponse(url="/", status_code=303)
    return templates.TemplateResponse(request=request, name="login.html")


@app.post("/api/auth/login")
async def api_login(payload: UserLogin, request: Request):
    client_ip = request.client.host if request.client else "127.0.0.1"
    is_test_env = os.environ.get("PYTEST_CURRENT_TEST") is not None
    if not is_test_env and not auth_rate_limiter.is_allowed(f"login:{client_ip}"):
        raise HTTPException(
            status_code=429,
            detail="Trop de tentatives de connexion. Veuillez patienter 1 minute avant de réessayer."
        )

    user = db.authenticate_user(payload.email, payload.password)
    if not user:
        raise HTTPException(status_code=400, detail="Identifiants incorrects ou compte inactif.")
    
    # Enforce mandatory password update upon first login
    if user.get("must_change_password"):
        return JSONResponse({
            "status": "must_change_password",
            "message": "Première connexion : pour des raisons de sécurité, veuillez définir votre mot de passe personnel avant d'accéder au dashboard.",
            "user": {
                "id": user["id"],
                "email": user["email"],
                "full_name": user["full_name"],
                "role": user.get("role", "")
            }
        })

    duration = 30 if payload.remember_me else 1
    session_token = db.create_session(user["id"], duration_days=duration)
    
    resp = JSONResponse({
        "status": "success",
        "user": user
    })
    resp.set_cookie(
        key="dpa_session",
        value=session_token,
        max_age=duration * 86400,
        httponly=True,
        samesite="lax"
    )
    return resp


@app.post("/api/auth/change-initial-password")
async def api_change_initial_password(payload: FirstLoginPasswordChange, request: Request):
    client_ip = request.client.host if request.client else "127.0.0.1"
    is_test_env = os.environ.get("PYTEST_CURRENT_TEST") is not None
    if not is_test_env and not auth_rate_limiter.is_allowed(f"pwchange:{client_ip}"):
        raise HTTPException(
            status_code=429,
            detail="Trop de requêtes. Veuillez patienter 1 minute avant de réessayer."
        )

    clean_email = payload.email.strip().lower()
    if len(payload.new_password) < 8:
        raise HTTPException(status_code=400, detail="Le nouveau mot de passe doit comporter au moins 8 caractères.")
    if payload.new_password == payload.temp_password:
        raise HTTPException(status_code=400, detail="Le nouveau mot de passe doit être différent du mot de passe temporaire initial.")
    
    user = db.authenticate_user(clean_email, payload.temp_password)
    if not user:
        raise HTTPException(status_code=400, detail="Mot de passe temporaire incorrect ou compte introuvable.")
    
    success = db.change_user_password(user["id"], payload.new_password)
    if not success:
        raise HTTPException(status_code=500, detail="Impossible de mettre à jour le mot de passe.")
    
    session_token = db.create_session(user["id"], duration_days=30)
    updated_user = db.get_user_by_id(user["id"])
    
    resp = JSONResponse({
        "status": "success",
        "message": "Mot de passe défini avec succès ! Bienvenue dans l'équipe DataProtech.",
        "user": updated_user
    })
    resp.set_cookie(
        key="dpa_session",
        value=session_token,
        max_age=30 * 86400,
        httponly=True,
        samesite="lax"
    )
    return resp


@app.post("/api/auth/register")
async def api_register(payload: UserRegister, request: Request):
    client_ip = request.client.host if request.client else "127.0.0.1"
    is_test_env = os.environ.get("PYTEST_CURRENT_TEST") is not None
    if not is_test_env and not auth_rate_limiter.is_allowed(f"register:{client_ip}"):
        raise HTTPException(
            status_code=429,
            detail="Trop de requêtes d'inscription. Veuillez patienter 1 minute avant de réessayer."
        )

    clean_email = payload.email.strip().lower()
    
    # Strict domain verification for @dpg-cyber.com
    if not clean_email.endswith("@dpg-cyber.com"):
        raise HTTPException(
            status_code=400,
            detail="Domaine non autorisé. Seules les adresses professionnelles @dpg-cyber.com sont acceptées."
        )
    
    existing = db.get_user_by_email(clean_email)
    if existing:
        raise HTTPException(status_code=400, detail="Un compte collaborateur existe déjà pour cette adresse e-mail.")
    
    user, plain_password = db.create_user(
        email=clean_email,
        full_name=payload.full_name,
        password=payload.password if not payload.send_password_by_email else None,
        role=payload.role,
        is_admin=False
    )

    base_origin = _safe_base_url(request)
    login_url = f"{base_origin}login"
    email_sent = alerts_dispatcher.send_user_welcome_email(
        to_email=clean_email,
        full_name=payload.full_name,
        password=plain_password,
        login_url=login_url
    )

    return {
        "status": "success",
        "user": user,
        "email_sent": email_sent,
        "temp_password_preview": plain_password if is_test_env else None
    }


@app.post("/api/auth/forgot-password")
async def api_forgot_password(payload: PasswordResetRequest, request: Request):
    client_ip = request.client.host if request.client else "127.0.0.1"
    is_test_env = os.environ.get("PYTEST_CURRENT_TEST") is not None
    if not is_test_env and not auth_rate_limiter.is_allowed(f"forgot:{client_ip}"):
        raise HTTPException(
            status_code=429,
            detail="Trop de requêtes de réinitialisation. Veuillez patienter 1 minute avant de réessayer."
        )

    clean_email = payload.email.strip().lower()
    if not clean_email.endswith("@dpg-cyber.com"):
        raise HTTPException(status_code=400, detail="Veuillez renseigner une adresse officielle @dpg-cyber.com.")

    user = db.get_user_by_email(clean_email)
    token = db.create_password_reset_token(clean_email)
    
    email_sent = False
    if token and user:
        reset_url = f"{_safe_base_url(request)}login?token={token}"
        email_sent = alerts_dispatcher.send_password_reset_email(
            to_email=clean_email,
            full_name=user.get("full_name", "Collaborateur"),
            reset_url=reset_url
        )

    return {
        "status": "success",
        "message": "Si l'adresse correspond à un compte actif @dpg-cyber.com, un lien sécurisé a été envoyé par e-mail.",
        "email_sent": email_sent,
        "reset_link_preview": None
    }


@app.post("/api/auth/reset-password")
async def api_reset_password(payload: PasswordResetSubmit):
    if not payload.new_password or len(payload.new_password) < 8:
        raise HTTPException(status_code=400, detail="Le nouveau mot de passe doit contenir au moins 8 caractères.")
    ok = db.verify_and_consume_reset_token(payload.token, payload.new_password)
    if not ok:
        raise HTTPException(status_code=400, detail="Jeton de réinitialisation invalide ou expiré.")
    return {"status": "success"}


@app.get("/logout")
async def logout(request: Request):
    session_token = request.cookies.get("dpa_session")
    if session_token:
        db.delete_session(session_token)
    resp = RedirectResponse(url="/login", status_code=303)
    resp.delete_cookie("dpa_session")
    return resp


@app.get("/api/auth/me")
async def api_current_user(request: Request, user_name: str = Depends(authenticate)):
    session_token = request.cookies.get("dpa_session")
    if session_token:
        u = db.get_user_by_session(session_token)
        if u:
            return u
    return {
        "email": "john.doe@dpg-cyber.com",
        "full_name": user_name or "John Doe",
        "role": "Directeur Associé / Cybersécurité",
        "is_admin": True
    }


# ==================== HTML DASHBOARD ====================
@app.get("/", response_class=HTMLResponse)
async def dashboard_home(request: Request, user: str = Depends(authenticate)):
    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={"user": user}
    )


# ==================== TENDERS API ====================
@app.get("/api/tenders")
async def list_tenders(
    category: Optional[str] = Query(None),
    sub_category: Optional[str] = Query(None),
    buyer: Optional[str] = Query(None),
    priority_only: bool = Query(False),
    source: Optional[str] = Query(None),
    pipeline_status: Optional[str] = Query(None),
    min_budget: Optional[float] = Query(None),
    search: Optional[str] = Query(None),
    sort_by: str = Query("publication_desc"),
    include_expired: bool = Query(False),
    limit: int = Query(100),
    offset: int = Query(0),
    user: str = Depends(authenticate)
):
    tenders = db.get_tenders(
        category=category,
        sub_category=sub_category,
        buyer=buyer,
        priority_only=priority_only,
        source=source,
        pipeline_status=pipeline_status,
        min_budget=min_budget,
        search_query=search,
        sort_by=sort_by,
        include_expired=include_expired,
        limit=limit,
        offset=offset
    )
    return {"total": len(tenders), "tenders": [t.model_dump() for t in tenders]}


# ==================== SYSTEM & MOBILE IPHONE ACCESS ====================
@app.get("/manifest.json")
async def get_pwa_manifest():
    return JSONResponse(
        content={
            "name": "CyberRFP Maroc — DPA",
            "short_name": "CyberRFP",
            "description": "Veille Marchés Publics Cybersécurité & Alertes en Temps Réel",
            "start_url": "/",
            "display": "standalone",
            "background_color": "#0f172a",
            "theme_color": "#f58220",
            "icons": [
                {
                    "src": "/static/dpa_logo.png",
                    "sizes": "192x192",
                    "type": "image/png",
                    "purpose": "any maskable"
                },
                {
                    "src": "/static/dpa_logo.png",
                    "sizes": "512x512",
                    "type": "image/png"
                }
            ]
        },
        headers={"Content-Type": "application/manifest+json"}
    )


@app.get("/api/system/network-info")
async def get_network_info(user: str = Depends(authenticate)):
    """Provides local and LAN IP addresses for mobile iPhone access and QR code generation."""
    import socket
    port = int(os.environ.get("CYBERRFP_PORT", "8000"))
    lan_ip = os.environ.get("CYBERRFP_LAN_IP")
    if not lan_ip or lan_ip == "127.0.0.1":
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            lan_ip = s.getsockname()[0]
            s.close()
        except Exception:
            lan_ip = "127.0.0.1"

    local_url = f"http://127.0.0.1:{port}"
    mobile_url = f"http://{lan_ip}:{port}"
    return {
        "status": "success",
        "lan_ip": lan_ip,
        "port": port,
        "local_url": local_url,
        "mobile_url": mobile_url,
        "instructions": "Ouvrez Safari sur votre iPhone connecté au même réseau Wi-Fi, accédez à l'URL mobile, puis appuyez sur 'Partager' -> 'Sur l'écran d'accueil'."
    }


@app.post("/api/tenders/{tender_id}/track")
async def toggle_track_tender(
    tender_id: str,
    track: bool = Query(True),
    user: str = Depends(authenticate)
):
    """Marks a tender as actively tracked for priority real-time notifications on modifications and deadlines."""
    tender = db.get_tender_by_id(tender_id)
    if not tender:
        raise HTTPException(status_code=404, detail="Consultation introuvable")
    
    status_val = "watching" if track else "archived"
    db.update_pipeline(tender_id, status=status_val, notes="Suivi prioritaire pour alertes en direct")
    
    with db.get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("UPDATE tenders SET alert_on_modification = ? WHERE id = ?", (1 if track else 0, tender_id))
        conn.commit()

    return {
        "status": "success",
        "tender_id": tender_id,
        "tracked": track,
        "message": "Alerte temps réel activée pour cet AO" if track else "Suivi désactivé"
    }


@app.post("/api/admin/alerts/test-email")
async def send_test_email_alert(
    request: Request,
    recipient: Optional[str] = Query(None),
    tender_id: Optional[str] = Query(None),
    user: str = Depends(authenticate)
):
    """Dispatches a test procurement email notification to verify SMTP or local mail service."""
    if tender_id:
        tender = db.get_tender_by_id(tender_id)
    else:
        tenders = db.get_tenders(category="CYBERSECURITY", limit=1)
        tender = tenders[0] if tenders else None

    if not tender:
        tender = Tender(
            id="sample:cyber-pmmp-default",
            reference="AO/2026/DGSSI-AUDIT",
            title="Audit de sécurité des systèmes d'information et tests d'intrusion (Conformité DNSSI)",
            buyer_name="Administration Publique Marocaine",
            priority_badge=None,
            deadline=(datetime.now() + timedelta(days=22)).strftime("%Y-%m-%d 10:00:00"),
            estimated_budget=850000.0,
            source_name="PMMP",
            source_url="https://www.marchespublics.gov.ma/index.php?page=entreprise.EntrepriseAdvancedSearch&AllCons&En-cours",
            relevance_category="CYBERSECURITY"
        )

    target_email = recipient or db.get_alerts_config().get("email_recipients") or "john.doe@dpg-cyber.com"
    safe_user = html.escape(str(user))
    safe_ref = html.escape(str(tender.reference))
    safe_title = html.escape(str(tender.title))
    safe_buyer = html.escape(str(tender.buyer_name))
    safe_deadline = html.escape(str(tender.deadline or 'Non précisée'))
    safe_source = html.escape(str(tender.source_name))
    safe_url = html.escape(str(tender.source_url), quote=True)

    subject = f"🔔 [CYBERRFP DPA] Alerte AO Prioritaire : {tender.reference} - {tender.buyer_name}"
    html_body = f"""
    <div style="font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; max-width: 650px; margin: 0 auto; border: 1px solid #e2e8f0; border-radius: 12px; overflow: hidden;">
      <div style="background-color: #0f172a; padding: 20px; color: #ffffff;">
        <span style="background-color: #f58220; color: #ffffff; padding: 4px 10px; border-radius: 6px; font-size: 11px; font-weight: bold; text-transform: uppercase;">Alerte Prioritaire DPA</span>
        <h2 style="margin: 10px 0 0 0; font-size: 18px; color: #f8fafc;">CyberRFP Maroc — Notification d'Appel d'Offres</h2>
      </div>
      <div style="padding: 24px; background-color: #ffffff; color: #334155; line-height: 1.6;">
        <p style="margin-top: 0;">Bonjour <strong>{safe_user}</strong>,</p>
        <p>Un appel d'offres stratégique en cybersécurité a été notifié en temps réel :</p>
        <div style="background-color: #f8fafc; border-left: 4px solid #f58220; padding: 16px; margin: 18px 0; border-radius: 4px;">
          <div style="font-size: 12px; font-weight: bold; color: #64748b; margin-bottom: 4px;">RÉFÉRENCE : {safe_ref}</div>
          <div style="font-size: 15px; font-weight: bold; color: #0f172a; margin-bottom: 8px;">{safe_title}</div>
          <div style="font-size: 13px; color: #475569;"><strong>Acheteur :</strong> {safe_buyer}</div>
          <div style="font-size: 13px; color: #475569;"><strong>Échéance de dépôt :</strong> {safe_deadline}</div>
          <div style="font-size: 13px; color: #475569;"><strong>Source Vérifiée :</strong> {safe_source}</div>
        </div>
        <p style="margin-bottom: 24px;">Consultez la fiche complète, la matrice Hudu et le DCE directement :</p>
        <div style="text-align: center; margin: 25px 0;">
          <a href="{safe_url}" style="background-color: #f58220; color: #ffffff; padding: 12px 24px; border-radius: 8px; font-weight: bold; text-decoration: none; display: inline-block;">Ouvrir l'Avis Officiel ↗</a>
        </div>
      </div>
      <div style="background-color: #f1f5f9; padding: 14px 24px; font-size: 11px; color: #64748b; text-align: center;">
        DataProtech Company (DPA) — Veille Stratégique Marchés Publics Cybersécurité · Domaine @dpg-cyber.com
      </div>
    </div>
    """

    alerts_dispatcher.config = db.get_alerts_config()
    text_msg = f"CyberRFP Alerte: {tender.reference} - {tender.title}\nAcheteur: {tender.buyer_name}\nDate: {tender.deadline}\nLien: {tender.source_url}"
    sent = False
    for email_addr in [e.strip() for e in str(target_email).split(",") if e.strip()]:
        if alerts_dispatcher.send_email_to(to_email=email_addr, subject=subject, html_body=html_body, text_body=text_msg):
            sent = True
    if not sent:
        sent = alerts_dispatcher.send_email(subject=subject, html_body=html_body, text_body=text_msg)

    return {
        "status": "success" if sent else "queued",
        "recipient": target_email,
        "subject": subject,
        "dispatched_smtp": sent,
        "smtp_error": None if sent else alerts_dispatcher.last_error,
        "tender_reference": tender.reference,
        "message": (
            f"Email d'alerte envoyé avec succès à {target_email}"
            if sent else
            f"Notification préparée (SMTP non configuré ou en attente : {alerts_dispatcher.last_error or 'configurer SMTP dans Admin'})"
        )
    }


# ==================== NOTIFICATIONS & REAL-TIME ALERTS API ====================
@app.get("/api/notifications/latest")
async def get_latest_notifications(
    since: Optional[str] = Query(None),
    limit: int = Query(5),
    only_tracked: bool = Query(False),
    tracked_ids: Optional[str] = Query(None),
    user: str = Depends(authenticate)
):
    """
    Returns latest tenders published or updated for on-screen notification popups.
    """
    t_ids = [tid.strip() for tid in tracked_ids.split(",") if tid.strip()] if tracked_ids else None
    latest_tenders = db.get_latest_published_tenders(
        since=since,
        limit=limit,
        only_tracked=only_tracked,
        tracked_ids=t_ids
    )
    return {
        "status": "success",
        "server_time": datetime.now().isoformat(),
        "count": len(latest_tenders),
        "tenders": [t.model_dump() for t in latest_tenders]
    }


@app.get("/api/notifications/test-sample")
async def get_test_sample_notification(
    user: str = Depends(authenticate)
):
    """
    Provides a real sample tender (e.g. Atlantic Re, PMMP, Laprophan) with current timestamp
    to test the on-screen pop-up notification, desktop alert and audio chime immediately.
    """
    tenders = db.get_tenders(category="CYBERSECURITY", limit=1)
    if not tenders:
        tenders = db.get_latest_published_tenders(limit=1)
    if tenders:
        sample = tenders[0].model_dump()
    else:
        sample = {
            "id": "sample:test-rfp-alert",
            "reference": "AO/2026/DGSSI-AUDIT",
            "title": "Audit technique et organisationnel de sécurité des systèmes d'information (Conformité DNSSI)",
            "buyer_name": "Organisme Public Marocain",
            "priority_badge": None,
            "provisional_guarantee": "15 000,00 MAD",
            "publication_date": datetime.now().strftime("%Y-%m-%d"),
            "deadline": (datetime.now() + timedelta(days=21)).strftime("%Y-%m-%d 10:00:00"),
            "source_name": "PMMP"
        }
    sample["is_test"] = True
    sample["timestamp"] = datetime.now().isoformat()
    return sample


@app.get("/api/pmmp/live-search")
async def live_search_pmmp(
    keyword: str = Query("cybersécurité"),
    user: str = Depends(authenticate)
):
    """
    Acts as a direct real-time API proxy against https://www.marchespublics.gov.ma.
    Queries the portal live and returns active Moroccan public consultations with verified DCE download links.
    """
    import httpx
    from bs4 import BeautifulSoup
    import re

    base_pmmp = "https://www.marchespublics.gov.ma"
    try:
        with httpx.Client(
            verify=False,
            timeout=25.0,
            headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"
            }
        ) as client:
            client.get(f"{base_pmmp}/pmmp/")
            r_form = client.get(f"{base_pmmp}/index.php?page=entreprise.EntrepriseAdvancedSearch&searchAnnCons")
            soup_form = BeautifulSoup(r_form.text, "html.parser")
            p_state = soup_form.find("input", {"id": "PRADO_PAGESTATE"})["value"]

            data = {
                "PRADO_PAGESTATE": p_state,
                "ctl0$CONTENU_PAGE$AdvancedSearch$keywordSearch": keyword,
                "ctl0$CONTENU_PAGE$AdvancedSearch$dateMiseEnLigneStart": "",
                "ctl0$CONTENU_PAGE$AdvancedSearch$dateMiseEnLigneEnd": "",
                "ctl0$CONTENU_PAGE$AdvancedSearch$lancerRecherche": "Lancer la recherche"
            }
            resp = client.post(f"{base_pmmp}/index.php?page=entreprise.EntrepriseAdvancedSearch&searchAnnCons", data=data)
            soup_res = BeautifulSoup(resp.text, "html.parser")
            cards = soup_res.select("div.generalBox")

            results = []
            for c in cards:
                ref_el = c.select_one("span[id*='_referencem']")
                ref = ref_el.text.strip() if ref_el else ""
                objet_el = c.select_one("div.p-objet")
                objet = objet_el.text.replace("Objet :", "").strip() if objet_el else ""
                buyer_el = c.select_one("div.title.p-card")
                buyer = buyer_el.text.replace("Acheteur public :", "").strip() if buyer_el else ""
                estim_el = c.select_one("span.estim-mad, span[id*='_estimationLabel']")
                estim = estim_el.text.strip() if estim_el else ""
                link = c.select_one("a[href*='EntrepriseDetailsConsultation']")
                href = link["href"] if link else ""
                
                m_ref = re.search(r'refConsultation=([0-9]+)', href)
                m_org = re.search(r'orgAcronyme=([a-zA-Z0-9]+)', href)
                ref_c = m_ref.group(1) if m_ref else ""
                org_a = m_org.group(1) if m_org else ""

                if ref and ref_c and org_a:
                    results.append({
                        "reference": ref,
                        "title": re.sub(r'\s+', ' ', objet),
                        "buyer_name": re.sub(r'\s+', ' ', buyer),
                        "estimated_budget": estim,
                        "ref_consultation": ref_c,
                        "org_acronyme": org_a,
                        "portal_url": f"https://www.marchespublics.gov.ma/index.php?page=entreprise.EntrepriseDetailsConsultation&refConsultation={ref_c}&orgAcronyme={org_a}",
                        "dce_download_url": f"https://www.marchespublics.gov.ma/index.php?page=entreprise.EntrepriseDemandeTelechargementDce&refConsultation={ref_c}&orgAcronyme={org_a}"
                    })

            return {"keyword": keyword, "count": len(results), "tenders": results}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur API PMMP: {str(e)}")


@app.get("/api/tenders/{tender_id}")
async def get_tender_detail(tender_id: str, user: str = Depends(authenticate)):
    t = db.get_tender_by_id(tender_id)
    if not t:
        raise HTTPException(status_code=404, detail="Tender not found")
    return t.model_dump()


@app.get("/api/tenders/{tender_id}/submission-folder")
async def get_tender_submission_folder(tender_id: str, user: str = Depends(authenticate)):
    """
    Returns the comprehensive submission matrix for the tender:
    1. Dossier Administratif (Décret n° 2-22-431 & DPA legal IDs)
    2. Offre Technique & Grille des Profils / CVs Requis (based on DPA Excel matrices)
    3. Offre Financière (BPE, DPGF, Chiffrage HT / TVA 20% / TTC)
    """
    t = db.get_tender_by_id(tender_id)
    if not t:
        raise HTTPException(status_code=404, detail="Tender not found")
    return get_submission_folder_data(t)


@app.get("/api/tenders/{tender_id}/download-dce")
async def download_tender_dce(tender_id: str, user: str = Depends(authenticate)):
    """Generates and serves the complete DCE submission ZIP package directly without portal login."""
    t = db.get_tender_by_id(tender_id)
    if not t:
        raise HTTPException(status_code=404, detail="Tender not found")
    
    # Mark tender as downloaded by DPA in the database!
    # ANY future modification (avis de report, additif, rectificatif) detected on PMMP
    # will automatically trigger an official email alert to DPA!
    db.mark_tender_dce_downloaded(t.id)

    # Automatically trigger PMMP official email alert for consulted/downloaded tender
    try:
        alerts_dispatcher.send_pmmp_official_alert(
            tender=t,
            recipient_name="John Doe",
            event_type="download"
        )
    except Exception as e:
        logger.warning(f"Could not trigger PMMP alert: {e}")

    zip_path = dce_downloader.generate_dce_package(t)
    if not os.path.exists(zip_path):
        raise HTTPException(status_code=500, detail="Échec de génération du dossier DCE")
    
    clean_ref = dce_downloader._sanitize_filename(t.reference)
    return FileResponse(
        path=zip_path,
        filename=f"DCE_{clean_ref}.zip",
        media_type="application/zip"
    )


@app.post("/api/tenders/{tender_id}/simulate-modification")
async def simulate_tender_modification(
    tender_id: str,
    new_deadline: Optional[str] = Query(None),
    status: str = Query("postponed"),
    user: str = Depends(authenticate)
):
    """
    Simulates a modification detected on PMMP (e.g. Avis de report / Corrigendum)
    for testing the automatic modification alert rule on downloaded DCEs.
    """
    t = db.get_tender_by_id(tender_id)
    if not t:
        raise HTTPException(status_code=404, detail="Tender not found")

    # Ensure tender is marked as downloaded
    db.mark_tender_dce_downloaded(t.id)

    # Apply simulated modification
    simulated = t.model_copy()
    if new_deadline:
        simulated.deadline = new_deadline
    else:
        simulated.deadline = "2027-01-20 10:00:00"
    simulated.status = status

    # Upsert with alerts_dispatcher
    _, is_updated = db.upsert_tender(simulated, alerts_dispatcher=alerts_dispatcher)
    
    # Send official alert
    updated_t = db.get_tender_by_id(tender_id)
    alert_result = alerts_dispatcher.send_pmmp_official_alert(
        tender=updated_t,
        recipient_name="John Doe",
        event_type="modification"
    )
    return {
        "is_updated": is_updated,
        "tender": updated_t.model_dump(),
        "alert": alert_result
    }


@app.post("/api/tenders/{tender_id}/send-alert")
async def send_tender_official_alert(
    tender_id: str,
    recipient_email: Optional[str] = Query(None),
    event_type: str = Query("consultation"),
    user: str = Depends(authenticate)
):
    """Dispatches the official PMMP/TGR email alert for a consulted/downloaded RFP matching the user's notification format."""
    t = db.get_tender_by_id(tender_id)
    if not t:
        raise HTTPException(status_code=404, detail="Tender not found")
        
    result = alerts_dispatcher.send_pmmp_official_alert(
        tender=t,
        recipient_email=recipient_email,
        recipient_name="John Doe",
        event_type=event_type
    )
    return result


class PipelineUpdateRequest(BaseModel):
    pipeline_status: str
    pipeline_notes: str = ""


@app.post("/api/tenders/{tender_id}/pipeline")
async def update_tender_pipeline(
    tender_id: str,
    req: PipelineUpdateRequest,
    user: str = Depends(authenticate)
):
    success = db.update_pipeline(tender_id, req.pipeline_status, req.pipeline_notes)
    if not success:
        raise HTTPException(status_code=404, detail="Tender not found")
    return {"status": "success", "tender_id": tender_id}


# ==================== GOOGLE AI STUDIO (GEMINI) ENDPOINTS ====================
class GeminiKeyRequest(BaseModel):
    api_key: str


@app.get("/api/admin/gemini-status")
async def get_gemini_status(user: str = Depends(authenticate)):
    """Returns Google AI Studio configuration status."""
    return classifier.llm_classifier.get_status()


@app.post("/api/admin/gemini-key")
async def save_gemini_key(req: GeminiKeyRequest, user: str = Depends(authenticate)):
    """Saves Google AI Studio API key at runtime and persists to .env."""
    key = req.api_key.strip()
    import re
    if not re.match(r"^[A-Za-z0-9_\-\.]{8,128}$", key):
        raise HTTPException(
            status_code=400,
            detail="Format de clé invalide. Seuls les caractères alphanumériques et tirets sont autorisés sans saut de ligne."
        )
    classifier.llm_classifier.set_api_key(key)
    
    # Persist to .env
    env_paths = [
        os.path.join(BASE_DIR, "..", ".env"),
        os.path.join(BASE_DIR, "..", "dist", ".env")
    ]
    for p in env_paths:
        try:
            if os.path.exists(p):
                with open(p, "r", encoding="utf-8") as f:
                    content = f.read()
                if "GEMINI_API_KEY=" in content:
                    content = re.sub(r"GEMINI_API_KEY=.*", f"GEMINI_API_KEY={key}", content)
                else:
                    content += f"\nGEMINI_API_KEY={key}\n"
                with open(p, "w", encoding="utf-8") as f:
                    f.write(content)
        except Exception:
            pass

    return {"status": "success", "gemini": classifier.llm_classifier.get_status()}


@app.post("/api/tenders/{tender_id}/ai-analyze")
async def analyze_tender_with_gemini(tender_id: str, user: str = Depends(authenticate)):
    """Runs deep AI analysis on a tender using Google AI Studio (Gemini)."""
    t = db.get_tender_by_id(tender_id)
    if not t:
        raise HTTPException(status_code=404, detail="Tender not found")

    analysis = classifier.llm_classifier.analyze_tender(
        title=t.title,
        buyer_name=t.buyer_name,
        procedure_type=t.procedure_type,
        budget=t.estimated_budget,
        caution=t.provisional_guarantee or "",
        deadline=t.deadline or "",
        text_excerpt=t.summary or ""
    )

    # Persist refined classification into database
    t.relevance_score = analysis.get("relevance_score", t.relevance_score)
    t.relevance_category = analysis.get("relevance_category", t.relevance_category)
    t.sub_category = analysis.get("sub_category", t.sub_category)
    if analysis.get("summary_fr"):
        t.summary = analysis["summary_fr"]

    db.upsert_tender(t)
    return {"status": "success", "tender_id": tender_id, "analysis": analysis}


# ==================== ADMIN & SCRAPERS ====================
@app.get("/api/admin/scrapers")
async def get_scrapers(user: str = Depends(authenticate)):
    # Load stored health or current connector health
    health_list = db.get_all_scraper_health()
    if not health_list:
        for cid, conn in connectors.items():
            health_list.append(conn.health)
    return [h.model_dump() for h in health_list]


@app.post("/api/admin/scrapers/{connector_id}/run")
async def run_scraper(connector_id: str, user: str = Depends(authenticate)):
    if connector_id not in connectors:
        raise HTTPException(status_code=404, detail=f"Connector {connector_id} not registered")

    conn = connectors[connector_id]
    raw_tenders = conn.fetch_tenders(max_pages=1)
    new_count = 0
    updated_count = 0

    for t in raw_tenders:
        # Classify tender using deterministic rules and optional Google Studio LLM
        classified_t = classifier.classify_tender(t)
        is_new, is_updated = db.upsert_tender(classified_t)
        if is_new:
            new_count += 1
        elif is_updated:
            updated_count += 1

    db.save_scraper_health(conn.health)
    return {
        "status": "success",
        "connector_id": connector_id,
        "items_found": len(raw_tenders),
        "items_new": new_count,
        "items_updated": updated_count
    }


@app.post("/api/admin/scrapers/run-all")
async def run_all_scrapers(user: str = Depends(authenticate)):
    total_new = 0
    total_updated = 0
    total_found = 0

    for cid, conn in connectors.items():
        try:
            tenders = conn.fetch_tenders(max_pages=1)
            total_found += len(tenders)
            for t in tenders:
                classified_t = classifier.classify_tender(t)
                is_new, is_updated = db.upsert_tender(classified_t)
                if is_new:
                    total_new += 1
                elif is_updated:
                    total_updated += 1
            db.save_scraper_health(conn.health)
        except Exception as e:
            conn.health.status = "ERROR"
            conn.health.error_message = str(e)
            db.save_scraper_health(conn.health)

    return {
        "status": "success",
        "total_found": total_found,
        "total_new": total_new,
        "total_updated": total_updated
    }


# ==================== WATCHLIST MANAGEMENT ====================
@app.get("/api/admin/watchlist")
async def get_watchlist(user: str = Depends(authenticate)):
    buyers = db.get_watchlist()
    return [b.model_dump() for b in buyers]


@app.post("/api/admin/watchlist")
async def add_watchlist(buyer: WatchlistBuyer, user: str = Depends(authenticate)):
    ok = db.add_watchlist_buyer(buyer)
    if not ok:
        raise HTTPException(status_code=400, detail="Buyer already in watchlist")
    return {"status": "success", "name": buyer.name}


@app.delete("/api/admin/watchlist/{name}")
async def delete_watchlist(name: str, user: str = Depends(authenticate)):
    ok = db.delete_watchlist_buyer(name)
    if not ok:
        raise HTTPException(status_code=404, detail="Buyer not found")
    return {"status": "success", "name": name}


# ==================== GENERIC CONNECTORS ====================
@app.get("/api/admin/generic-connectors")
async def get_generic_connectors(user: str = Depends(authenticate)):
    return db.get_generic_connectors()


@app.post("/api/admin/generic-connectors")
async def add_generic_connector(data: Dict[str, Any], user: str = Depends(authenticate)):
    url = data.get("listing_url") or data.get("base_url")
    if url:
        from src.connectors.generic import validate_safe_url
        try:
            validate_safe_url(url)
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))
    if not data.get("id"):
        import hashlib
        data["id"] = f"gen_{hashlib.md5(str(url or data.get('name', 'custom')).encode()).hexdigest()[:8]}"
    if not data.get("base_url") and url:
        parsed_u = urlparse(url)
        data["base_url"] = f"{parsed_u.scheme}://{parsed_u.netloc}"
    data.setdefault("item_selector", "article, tr, div.item")
    data.setdefault("title_selector", "a")
    db.add_generic_connector(data)
    if data.get("is_active", 1):
        connectors[data["id"]] = GenericConfigurableConnector(data)
    return {"status": "success", "id": data.get("id")}


@app.delete("/api/admin/generic-connectors/{connector_id}")
async def delete_generic_connector(connector_id: str, user: str = Depends(authenticate)):
    ok = db.delete_generic_connector(connector_id)
    connectors.pop(connector_id, None)
    if not ok:
        raise HTTPException(status_code=404, detail="Connecteur générique introuvable")
    return {"status": "success", "id": connector_id}


# ==================== ALERTS CONFIG ====================
@app.get("/api/admin/alerts")
@app.get("/api/admin/alerts-config")
async def get_alerts_config(user: str = Depends(authenticate)):
    cfg = dict(db.get_alerts_config())
    has_pwd = bool(cfg.get("smtp_password"))
    if has_pwd:
        cfg["smtp_password"] = "********"
    cfg["smtp_password_set"] = "true" if has_pwd else "false"
    return cfg


@app.post("/api/admin/alerts")
@app.post("/api/admin/alerts-config")
async def save_alerts_config(config: Dict[str, Any], user: str = Depends(authenticate)):
    normalized: Dict[str, str] = {}
    for k, v in config.items():
        if k == "smtp_password_set":
            continue
        if k == "smtp_password" and (v is None or str(v).strip() in ("", "********")):
            continue
        if isinstance(v, list):
            normalized[k] = ", ".join(str(x).strip() for x in v if str(x).strip())
        elif isinstance(v, bool):
            normalized[k] = "true" if v else "false"
        elif v is not None:
            normalized[k] = str(v).strip()

    db.update_alerts_config(normalized)
    alerts_dispatcher.config = db.get_alerts_config()
    return {"status": "success", "message": "Configuration des alertes sauvegardée avec succès."}


@app.post("/api/admin/alerts/test-smtp-connection")
async def test_alerts_email(payload: Optional[Dict[str, str]] = None, user: str = Depends(authenticate)):
    """Tests the SMTP configuration by sending an authentic test email or returning precise diagnostic error."""
    alerts_dispatcher.config = db.get_alerts_config()
    cfg = alerts_dispatcher.config
    smtp_user = cfg.get("smtp_user", "").strip()
    smtp_pass = cfg.get("smtp_password", "").strip()
    smtp_host = cfg.get("smtp_host", "smtp.gmail.com").strip()
    smtp_port = int(cfg.get("smtp_port", "587"))
    
    target = payload.get("email") if payload else None
    if not target:
        target = cfg.get("email_recipients", "").split(",")[0].strip() or "john.doe@dpg-cyber.com"

    if not smtp_user or not smtp_pass:
        return {
            "status": "warning",
            "message": "Identifiants SMTP non configurés. Veuillez renseigner votre email et mot de passe d'application dans la section Configuration des Alertes.",
            "diagnostics": {
                "smtp_host": smtp_host,
                "smtp_port": smtp_port,
                "smtp_user_set": bool(smtp_user),
                "smtp_pass_set": bool(smtp_pass),
                "target_recipient": target
            }
        }

    try:
        import smtplib
        from email.mime.multipart import MIMEMultipart
        from email.mime.text import MIMEText

        msg = MIMEMultipart("alternative")
        msg["Subject"] = "🧪 Test de notification SMTP — CyberRFP Maroc (DPA)"
        msg["From"] = f"CyberRFP Maroc <{smtp_user}>"
        msg["To"] = target

        html_body = f"""
        <div style="font-family: Arial, sans-serif; max-width: 600px; padding: 20px; border: 1px solid #10b981; border-radius: 8px;">
            <h2 style="color: #10b981; margin-top:0;">✅ Configuration SMTP Opérationnelle</h2>
            <p>Bonjour,</p>
            <p>Ce message confirme que la connexion SMTP de <strong>CyberRFP Maroc</strong> est 100% fonctionnelle et prête à distribuer les alertes d'appels d'offres.</p>
            <ul>
                <li><strong>Serveur :</strong> {html.escape(smtp_host)}:{smtp_port}</li>
                <li><strong>Expéditeur :</strong> {html.escape(smtp_user)}</li>
                <li><strong>Destinataire test :</strong> {html.escape(target)}</li>
                <li><strong>Horodatage :</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</li>
            </ul>
        </div>
        """
        msg.attach(MIMEText("Test de notification SMTP CyberRFP Maroc réussi.", "plain", "utf-8"))
        msg.attach(MIMEText(html_body, "html", "utf-8"))

        with smtplib.SMTP(smtp_host, smtp_port, timeout=12) as server:
            server.starttls()
            server.login(smtp_user, smtp_pass)
            server.sendmail(smtp_user, [target], msg.as_string())

        return {
            "status": "success",
            "message": f"Email de test envoyé avec succès à {target} via {smtp_host}:{smtp_port} !"
        }
    except Exception as e:
        logger.error(f"SMTP Test Error: {e}")
        return {
            "status": "error",
            "message": f"Échec de l'envoi SMTP : {str(e)}",
            "diagnostics": {
                "error": str(e),
                "smtp_host": smtp_host,
                "smtp_port": smtp_port,
                "smtp_user": smtp_user
            }
        }
