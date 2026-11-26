# CyberRFP Maroc - Implementation Plan

> **Goal:** Build a production-ready, modular web application that monitors Moroccan public procurement platforms (PMMP, Al Barid Bank, OFPPT, SOREC, and generic custom buyers), identifies cybersecurity tenders using high-precision keyword rules and Google AI Studio (Gemini) LLM passes, provides an interactive trilingual dashboard (FR/AR/EN) with pipeline tracking, and dispatches multi-channel alerts (Email, Telegram/WhatsApp webhooks).

## Tech Stack
- **Backend**: Python 3.14 / FastAPI, Pydantic v2, APScheduler, httpx, BeautifulSoup4, PyMuPDF (PDF extraction)
- **AI / LLM**: Google GenAI SDK (`google-genai`) for Google AI Studio Gemini API integration with fallback to deterministic keyword classifier
- **Database**: SQLite (built-in, zero-dependency) with PostgreSQL connection string support
- **Frontend**: Responsive Tailwind CSS / Flowbite UI rendered via FastAPI + Jinja2 with live AJAX, multilingual i18n (FR, AR, EN), interactive pipeline board, and real-time filtering
- **Deployment**: Docker Compose + Dockerfile

---

## Phased Execution Roadmap

### Step 1: PMMP Connector (`src/connectors/pmmp.py`)
- Session cookie initialization (`/pmmp/`)
- Public search querying (`EntrepriseAdvancedSearch`) with keyword and buyer filtering
- HTML parsing using verified selectors (`div.generalBox`, `.hotTender`, `span[id*="_referencem"]`, `.p-objet`, `.estim-mad`, `.title.p-card`, `.limita.p-card`)
- Consultation detail retrieval (`EntrepriseDetailsConsultation`) extracting caution provisoire, bid opening date/place, qualifications, contact
- Anonymous DCE downloading support
- **Verification**: Run against live `marchespublics.gov.ma` and verify live tenders.

### Step 2: Cybersecurity Classifier & Google Studio LLM Engine (`src/classifier/`)
- Deterministic multilingual keyword matcher (French, English, Arabic)
- Negative filters (sécurité incendie, gardiennage, etc.)
- Provider-agnostic Google AI Studio (`google-genai`) integration with prompt engineering for relevance scoring (0-100), sub-category tag, and French executive summary
- Unit test suite with real positive & negative procurement examples.

### Step 3: Database & Dashboard Core (`src/database.py`, `src/server.py`, `src/templates/`)
- Data models for tenders, buyers, watchlist, sources, documents, timeline changes, pipeline status
- Deduplication and corrigenda/postponement linker
- FastAPI routes and modern UI:
  - Open cyber tenders sorted by deadline
  - Filter by priority buyer, sub-category, budget, deadline, source
  - Search bar
  - Trilingual UI toggle (FR, AR, EN)
  - Detail modal with full extracted metadata and documents
  - Pipeline tracker (watching, go, no-go, submitted, won, lost)
  - CSV/Excel export
  - Basic Auth

### Step 4: Al Barid Bank Connector (`src/connectors/albaridbank.py`)
- Ingestion of live public opportunities from `fournisseurs.albaridbank.ma` (JAGGAER `table.list-table`)
- Ingestion of institutional notices/PDFs from `www.albaridbank.ma`
- **Verification**: Run against live ABB platform and display real results.

### Step 5: Alerts & Scheduled Digest (`src/alerts/`)
- Multi-channel notification engine:
  - SMTP Email
  - Telegram / WhatsApp compatible Webhook
- Notification types:
  - Immediate new tender alert
  - Corrigendum / postponement alert
  - Deadline reminders at J-7, J-3, J-1 (Casablanca timezone)
- Daily Digest at 08:00 Africa/Casablanca time via APScheduler

### Step 6: Remaining Connectors (`src/connectors/`)
- OFPPT Connector (`ofppt.py`): direct health checker + PMMP dedicated filter
- SOREC Connector (`sorec.py`): direct scrape of `https://www.sorec.ma/appels-offres/`
- Generic Configurable Connector (`generic.py`): runtime URL + CSS selector scraping configurable via Admin UI

### Step 7: Admin UI & Scraper Health
- Admin dashboard to inspect scraper health, last success, error logs, and zero-result alerts
- Watchlist manager (add/edit priority buyers with fuzzy matching)
- Keywords manager (add positive/negative keywords)
- Manual "Run Now" connector trigger button

### Step 8: Comprehensive Tests, Docker, and Documentation
- Pytest suite (classifier, connectors, parsers, database)
- Dockerfile & docker-compose.yml
- Production README.md
