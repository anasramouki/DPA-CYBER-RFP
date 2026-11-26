"""
Database Management Layer for CyberRFP Maroc
Supports SQLite (zero-config local default) and PostgreSQL.
Handles tender ingestion, deduplication, history tracking, and configuration persistence.
"""
import sqlite3
import json
import os
import re
import hashlib
import secrets
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any, Tuple
from src.models import Tender, TenderChange, ScraperHealth, WatchlistBuyer, DocumentItem
from src.utils.watchlist import DEFAULT_PRIORITY_WATCHLIST, match_buyer_watchlist


def hash_password(password: str, salt: Optional[str] = None) -> Tuple[str, str]:
    if not salt:
        salt = secrets.token_hex(16)
    key = hashlib.pbkdf2_hmac(
        'sha256',
        password.encode('utf-8'),
        salt.encode('utf-8'),
        100000
    )
    return key.hex(), salt


def verify_password(password: str, password_hash: str, salt: str) -> bool:
    new_hash, _ = hash_password(password, salt)
    return secrets.compare_digest(new_hash, password_hash)


class Database:
    def __init__(self, db_path: Optional[str] = None):
        import sys
        if db_path:
            self.db_path = db_path
        elif os.environ.get("DATABASE_PATH"):
            self.db_path = os.environ.get("DATABASE_PATH")
        elif getattr(sys, "frozen", False):
            # When packaged into an exe, store db in the same directory as the executable
            exe_dir = os.path.dirname(sys.executable)
            self.db_path = os.path.join(exe_dir, "cyberrfp.db")
        else:
            self.db_path = os.path.join(
                os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "cyberrfp.db"
            )
        self.init_schema()
        self._seed_initial_data()

    def get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def init_schema(self):
        """Creates tables for tenders, changes timeline, scraper health, watchlist, and admin settings."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Tenders Table
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS tenders (
                id TEXT PRIMARY KEY,
                reference TEXT NOT NULL,
                title TEXT NOT NULL,
                buyer_name TEXT NOT NULL,
                buyer_normalized TEXT,
                is_priority_buyer INTEGER DEFAULT 0,
                priority_badge TEXT,
                procedure_type TEXT,
                category TEXT,
                lots TEXT,
                publication_date TEXT,
                deadline TEXT,
                bid_opening_date TEXT,
                bid_opening_place TEXT,
                estimated_budget REAL DEFAULT 0.0,
                provisional_guarantee TEXT,
                qualifications TEXT,
                agrements TEXT,
                contact TEXT,
                source_name TEXT,
                source_url TEXT,
                document_links TEXT,
                status TEXT DEFAULT 'open',
                relevance_category TEXT DEFAULT 'NOT_RELEVANT',
                relevance_score INTEGER DEFAULT 0,
                sub_category TEXT,
                summary TEXT,
                matched_keywords TEXT,
                pipeline_status TEXT DEFAULT 'watching',
                pipeline_notes TEXT DEFAULT '',
                dce_downloaded INTEGER DEFAULT 0,
                dce_downloaded_at TEXT,
                alert_on_modification INTEGER DEFAULT 0,
                first_seen_at TEXT,
                last_updated_at TEXT
            )
            """)

            # Dynamic migration for existing databases
            for col_def in [
                ("dce_downloaded", "INTEGER DEFAULT 0"),
                ("dce_downloaded_at", "TEXT"),
                ("alert_on_modification", "INTEGER DEFAULT 0")
            ]:
                try:
                    cursor.execute(f"ALTER TABLE tenders ADD COLUMN {col_def[0]} {col_def[1]}")
                except Exception:
                    pass

            # History / Corrigenda Timeline
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS tender_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                tender_id TEXT NOT NULL,
                timestamp TEXT NOT NULL,
                field_changed TEXT NOT NULL,
                old_value TEXT,
                new_value TEXT,
                change_type TEXT,
                FOREIGN KEY (tender_id) REFERENCES tenders (id) ON DELETE CASCADE
            )
            """)

            # Scraper Health Table
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS scraper_health (
                connector_id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                url TEXT NOT NULL,
                status TEXT DEFAULT 'HEALTHY',
                last_run_time TEXT,
                last_success_time TEXT,
                items_found_last_run INTEGER DEFAULT 0,
                total_items_indexed INTEGER DEFAULT 0,
                error_message TEXT
            )
            """)

            # Priority Buyers Watchlist
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS watchlist (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL,
                normalized_keywords TEXT NOT NULL,
                badge_label TEXT NOT NULL,
                category TEXT,
                notes TEXT
            )
            """)

            # Keywords Configuration
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS keywords (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                keyword TEXT UNIQUE NOT NULL,
                keyword_type TEXT NOT NULL,
                category_tag TEXT
            )
            """)

            # Generic Connectors Configuration
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS generic_connectors (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                base_url TEXT NOT NULL,
                listing_url TEXT NOT NULL,
                item_selector TEXT NOT NULL,
                ref_selector TEXT,
                title_selector TEXT NOT NULL,
                deadline_selector TEXT,
                budget_selector TEXT,
                doc_link_selector TEXT,
                is_active INTEGER DEFAULT 1
            )
            """)

            # Alerts Configuration
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS alerts_config (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL
            )
            """)

            # Users Table (Team members @dpg-cyber.com)
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id TEXT PRIMARY KEY,
                email TEXT UNIQUE NOT NULL,
                full_name TEXT NOT NULL,
                password_hash TEXT NOT NULL,
                salt TEXT NOT NULL,
                role TEXT DEFAULT 'Consultant Cybersécurité',
                is_active INTEGER DEFAULT 1,
                is_admin INTEGER DEFAULT 0,
                must_change_password INTEGER DEFAULT 0,
                reset_token TEXT,
                reset_token_expiry TEXT,
                created_at TEXT,
                last_login TEXT
            )
            """)

            # Dynamic migration for must_change_password
            try:
                cursor.execute("ALTER TABLE users ADD COLUMN must_change_password INTEGER DEFAULT 0")
            except Exception:
                pass

            # User Sessions Table
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS user_sessions (
                session_token TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                created_at TEXT,
                expires_at TEXT,
                FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
            )
            """)

            conn.commit()

    def _seed_initial_data(self):
        """Seeds default watchlist and keywords if empty."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            # Ensure all default priority watchlist buyers exist
            for b in DEFAULT_PRIORITY_WATCHLIST:
                cursor.execute("SELECT COUNT(*) FROM watchlist WHERE name = ?", (b.name,))
                if cursor.fetchone()[0] == 0:
                    cursor.execute("""
                    INSERT INTO watchlist (name, normalized_keywords, badge_label, category)
                    VALUES (?, ?, ?, ?)
                    """, (b.name, json.dumps(b.normalized_keywords), b.badge_label, b.category))

            # Default alerts config
            cursor.execute("SELECT COUNT(*) FROM alerts_config")
            if cursor.fetchone()[0] == 0:
                default_alerts = {
                    "email_enabled": "false",
                    "email_recipients": "vendor@cybersecurity.ma",
                    "smtp_host": "smtp.gmail.com",
                    "smtp_port": "587",
                    "smtp_user": "",
                    "smtp_password": "",
                    "webhook_enabled": "true",
                    "webhook_url": "https://api.telegram.org/botTOKEN/sendMessage",
                    "webhook_type": "telegram",
                    "daily_digest_time": "08:00"
                }
                for k, v in default_alerts.items():
                    cursor.execute("INSERT OR REPLACE INTO alerts_config (key, value) VALUES (?, ?)", (k, v))

            # Default Users (@dpg-cyber.com)
            admin_pass = os.environ.get("ADMIN_PASSWORD", "cyberrfp2026")
            
            # Anonymize any existing records
            cursor.execute("UPDATE users SET email = 'john.doe@dpg-cyber.com', full_name = 'John Doe' WHERE email LIKE '%anas%'")

            # Ensure john.doe@dpg-cyber.com exists
            cursor.execute("SELECT COUNT(*) FROM users WHERE LOWER(email) = 'john.doe@dpg-cyber.com'")
            if cursor.fetchone()[0] == 0:
                jdoe_hash, jdoe_salt = hash_password(admin_pass)
                cursor.execute("""
                INSERT INTO users (id, email, full_name, password_hash, salt, role, is_active, is_admin, must_change_password, created_at)
                VALUES (?, ?, ?, ?, ?, ?, 1, 1, 0, ?)
                """, (
                    f"usr_{secrets.token_hex(6)}",
                    "john.doe@dpg-cyber.com",
                    "John Doe",
                    jdoe_hash,
                    jdoe_salt,
                    "Directeur Associé / Cybersécurité",
                    datetime.now().isoformat()
                ))

            # Ensure admin@dpg-cyber.com exists
            cursor.execute("SELECT COUNT(*) FROM users WHERE LOWER(email) = 'admin@dpg-cyber.com'")
            if cursor.fetchone()[0] == 0:
                adm_hash, adm_salt = hash_password(admin_pass)
                cursor.execute("""
                INSERT INTO users (id, email, full_name, password_hash, salt, role, is_active, is_admin, must_change_password, created_at)
                VALUES (?, ?, ?, ?, ?, ?, 1, 1, 0, ?)
                """, (
                    f"usr_{secrets.token_hex(6)}",
                    "admin@dpg-cyber.com",
                    "Administrateur DPG",
                    adm_hash,
                    adm_salt,
                    "Administrateur Plateforme",
                    datetime.now().isoformat()
                ))

            conn.commit()

    @staticmethod
    def _sanitize_text(text: Optional[str]) -> str:
        """Cleans legacy PMMP labels and PUA Wingdings glyph prefixes."""
        if not text:
            return ""
        cleaned = re.sub(r"[\ue000-\uf8ff]", " ", text)
        cleaned = re.sub(r"^\s*(?:Objet|Acheteur\s+public)\s*:\s*", "", cleaned, flags=re.I)
        cleaned = re.sub(r"^[\s\-•·*:\ue000-\uf8ff]+", "", cleaned)
        return re.sub(r"\s+", " ", cleaned).strip()

    def cleanup_polluted_tenders(self, classifier=None) -> Dict[str, int]:
        """Removes legacy synthetic blog-URL press rows and normalizes PMMP prefixes."""
        removed = 0
        normalized = 0
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                DELETE FROM tenders
                WHERE id LIKE 'press:atlanticre-%'
                   OR id LIKE 'press:laprophan-%'
                   OR source_url LIKE '%sap-connect-day%'
                   OR source_url LIKE '%flowlink%'
                   OR source_url LIKE '%journee-dediee-a-la-cybersecurite%'
                   OR source_url LIKE '%academy-reunit%'
            """)
            removed = cursor.rowcount

            cursor.execute("SELECT id, title, buyer_name, buyer_normalized FROM tenders")
            rows = cursor.fetchall()
            for r in rows:
                clean_title = self._sanitize_text(r["title"])
                clean_buyer = self._sanitize_text(r["buyer_name"]) or "Organisme Public"
                if clean_title != (r["title"] or "") or clean_buyer != (r["buyer_name"] or ""):
                    is_prio, norm_buyer, badge = match_buyer_watchlist(clean_buyer)
                    final_norm = norm_buyer or clean_buyer
                    if classifier:
                        from src.classifier.rules import classify_text_rules
                        cat, score, subcat, kws = classify_text_rules(clean_title)
                        cursor.execute("""
                            UPDATE tenders
                            SET title = ?, buyer_name = ?, buyer_normalized = ?,
                                is_priority_buyer = ?, priority_badge = ?,
                                relevance_category = ?, relevance_score = ?,
                                sub_category = ?, matched_keywords = ?
                            WHERE id = ?
                        """, (
                            clean_title, clean_buyer, final_norm,
                            1 if is_prio else 0, badge,
                            cat, score, subcat, json.dumps(kws),
                            r["id"]
                        ))
                    else:
                        cursor.execute("""
                            UPDATE tenders
                            SET title = ?, buyer_name = ?, buyer_normalized = ?,
                                is_priority_buyer = ?, priority_badge = ?
                            WHERE id = ?
                        """, (
                            clean_title, clean_buyer, final_norm,
                            1 if is_prio else 0, badge,
                            r["id"]
                        ))
                    normalized += 1
            conn.commit()
        return {"removed": removed, "normalized": normalized}

    def upsert_tender(self, tender: Tender, alerts_dispatcher=None) -> Tuple[bool, bool]:
        """
        Inserts or updates a tender. Handles deduplication across sources.
        Detects corrigenda/postponements/amendments on the Moroccan procurement portal.
        Returns: (is_new, is_updated)
        CRITICAL RULE: If a tender's DCE was downloaded on the portal (dce_downloaded == 1),
        ANY modification triggers an automatic PMMP email alert!
        """
        tender.title = self._sanitize_text(tender.title) or tender.title
        tender.buyer_name = self._sanitize_text(tender.buyer_name) or tender.buyer_name
        is_prio_w, norm_w, badge_w = match_buyer_watchlist(tender.buyer_name)
        if norm_w:
            tender.buyer_normalized = norm_w
            tender.is_priority_buyer = is_prio_w
            tender.priority_badge = badge_w
        elif tender.buyer_normalized and tender.buyer_normalized.lower().startswith("acheteur public"):
            tender.buyer_normalized = tender.buyer_name

        now_str = datetime.now().isoformat()
        with self.get_connection() as conn:
            cursor = conn.cursor()

            # Check if tender already exists by ID or by (reference, buyer_normalized)
            cursor.execute("""
            SELECT * FROM tenders WHERE id = ? OR (reference = ? AND buyer_normalized = ?)
            """, (tender.id, tender.reference, tender.buyer_normalized))
            existing = cursor.fetchone()

            if not existing:
                # Insert brand new tender
                cursor.execute("""
                INSERT INTO tenders (
                    id, reference, title, buyer_name, buyer_normalized, is_priority_buyer,
                    priority_badge, procedure_type, category, lots, publication_date, deadline,
                    bid_opening_date, bid_opening_place, estimated_budget, provisional_guarantee,
                    qualifications, agrements, contact, source_name, source_url, document_links,
                    status, relevance_category, relevance_score, sub_category, summary,
                    matched_keywords, pipeline_status, pipeline_notes, dce_downloaded, dce_downloaded_at,
                    alert_on_modification, first_seen_at, last_updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    tender.id, tender.reference, tender.title, tender.buyer_name, tender.buyer_normalized,
                    1 if tender.is_priority_buyer else 0, tender.priority_badge, tender.procedure_type,
                    tender.category, tender.lots, tender.publication_date, tender.deadline,
                    tender.bid_opening_date, tender.bid_opening_place, tender.estimated_budget,
                    tender.provisional_guarantee, tender.qualifications, tender.agrements, tender.contact,
                    tender.source_name, tender.source_url, json.dumps([d.model_dump() for d in tender.document_links]),
                    tender.status, tender.relevance_category, tender.relevance_score, tender.sub_category,
                    tender.summary, json.dumps(tender.matched_keywords), tender.pipeline_status,
                    tender.pipeline_notes, 1 if tender.dce_downloaded else 0, tender.dce_downloaded_at,
                    1 if tender.alert_on_modification else 0, now_str, now_str
                ))

                # Log initial discovery in history
                cursor.execute("""
                INSERT INTO tender_history (tender_id, timestamp, field_changed, new_value, change_type)
                VALUES (?, ?, ?, ?, ?)
                """, (tender.id, now_str, "status", tender.status, "discovery"))

                conn.commit()
                return True, False

            else:
                # Tender exists: check for changes (e.g. deadline postponement, corrigendum, document added)
                existing_id = existing["id"]
                updated = False
                
                # Check if this tender's DCE was downloaded on PMMP
                was_downloaded = bool(existing["dce_downloaded"]) if "dce_downloaded" in existing.keys() else False
                alert_enabled = bool(existing["alert_on_modification"]) if "alert_on_modification" in existing.keys() else False

                # 1. Check Deadline Postponement (Avis de report)
                if tender.deadline and tender.deadline != existing["deadline"]:
                    cursor.execute("""
                    INSERT INTO tender_history (tender_id, timestamp, field_changed, old_value, new_value, change_type)
                    VALUES (?, ?, ?, ?, ?, ?)
                    """, (existing_id, now_str, "deadline", existing["deadline"], tender.deadline, "postponement"))
                    cursor.execute("UPDATE tenders SET deadline = ?, status = 'postponed' WHERE id = ?", (tender.deadline, existing_id))
                    updated = True

                # 2. Check Status Change (Corrigendum / Rectificatif)
                if tender.status != existing["status"] and tender.status != "open":
                    cursor.execute("""
                    INSERT INTO tender_history (tender_id, timestamp, field_changed, old_value, new_value, change_type)
                    VALUES (?, ?, ?, ?, ?, ?)
                    """, (existing_id, now_str, "status", existing["status"], tender.status, "corrigendum"))
                    cursor.execute("UPDATE tenders SET status = ? WHERE id = ?", (tender.status, existing_id))
                    updated = True

                # 3. Merge Document Links (Nouveau document de consultation / Additif au DCE)
                old_docs_raw = existing["document_links"]
                old_docs = json.loads(old_docs_raw) if old_docs_raw else []
                old_urls = {d["url"] for d in old_docs if "url" in d}
                new_docs = [d.model_dump() for d in tender.document_links]
                merged_docs = list(old_docs)
                new_doc_found = False
                for nd in new_docs:
                    if nd.get("url") not in old_urls:
                        merged_docs.append(nd)
                        new_doc_found = True
                        updated = True

                if new_doc_found:
                    cursor.execute("""
                    INSERT INTO tender_history (tender_id, timestamp, field_changed, old_value, new_value, change_type)
                    VALUES (?, ?, ?, ?, ?, ?)
                    """, (existing_id, now_str, "document_links", f"{len(old_docs)} docs", f"{len(merged_docs)} docs", "additif_dce"))

                # 4. Check Title / Estimation change
                if tender.estimated_budget and tender.estimated_budget != existing["estimated_budget"]:
                    cursor.execute("UPDATE tenders SET estimated_budget = ? WHERE id = ?", (tender.estimated_budget, existing_id))
                    updated = True

                # Update timestamp, source URL/name, and docs
                cursor.execute("""
                UPDATE tenders SET
                    title = COALESCE(?, title),
                    source_name = COALESCE(?, source_name),
                    source_url = COALESCE(?, source_url),
                    summary = COALESCE(?, summary),
                    document_links = ?,
                    last_updated_at = ?
                WHERE id = ?
                """, (tender.title, tender.source_name, tender.source_url, tender.summary, json.dumps(merged_docs), now_str, existing_id))

                conn.commit()

                # AUTOMATIC TRIGGER: For EVERY tender on the portal:
                # A modification = automatic email alert IF the DCE was downloaded on PMMP!
                if updated and was_downloaded and alerts_dispatcher:
                    updated_tender = self.get_tender_by_id(existing_id)
                    if updated_tender:
                        try:
                            alerts_dispatcher.send_pmmp_official_alert(
                                tender=updated_tender,
                                recipient_name="John Doe",
                                event_type="modification"
                            )
                        except Exception:
                            pass

                return False, updated

    def mark_tender_dce_downloaded(self, tender_id: str) -> bool:
        """
        Marks a tender as having its DCE downloaded by DPA.
        From this moment on, ANY modification on the portal for this tender
        will automatically send an official PMMP alert email to DPA.
        """
        now_str = datetime.now().isoformat()
        with self.get_connection() as conn:
            cursor = conn.cursor()
            # Guard: only enable modification alert if tender is relevant to cybersecurity
            cursor.execute("SELECT relevance_category, relevance_score FROM tenders WHERE id = ?", (tender_id,))
            row = cursor.fetchone()
            is_relevant = row and row["relevance_category"] != "NOT_RELEVANT" and (row["relevance_score"] or 0) >= 40
            alert_val = 1 if is_relevant else 0

            cursor.execute("""
            UPDATE tenders SET 
                dce_downloaded = 1,
                dce_downloaded_at = ?,
                alert_on_modification = ?
            WHERE id = ?
            """, (now_str, alert_val, tender_id))
            conn.commit()
            return cursor.rowcount > 0

    def get_tenders(
        self,
        category: Optional[str] = None,
        sub_category: Optional[str] = None,
        buyer: Optional[str] = None,
        priority_only: bool = False,
        source: Optional[str] = None,
        pipeline_status: Optional[str] = None,
        min_budget: Optional[float] = None,
        search_query: Optional[str] = None,
        sort_by: str = "publication_desc",
        include_expired: bool = False,
        limit: int = 100,
        offset: int = 0
    ) -> List[Tender]:
        """Queries tenders with multi-faceted filtering, sorting by latest released (publication date) or deadline.
        By default excludes expired tenders where the deadline was yesterday or earlier."""
        query = "SELECT * FROM tenders WHERE 1=1"
        params: List[Any] = []

        if not include_expired:
            # Exclude tenders whose submission deadline has already elapsed
            now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            query += " AND (deadline IS NULL OR deadline = '' OR deadline >= ?)"
            params.append(now_str)

        if category:
            query += " AND relevance_category = ?"
            params.append(category)

        if sub_category:
            query += " AND sub_category = ?"
            params.append(sub_category)

        if buyer:
            query += " AND (buyer_name LIKE ? OR buyer_normalized LIKE ?)"
            params.extend([f"%{buyer}%", f"%{buyer}%"])

        if priority_only:
            query += " AND is_priority_buyer = 1"

        if source:
            source_lower = source.lower().strip()
            if "presse" in source_lower or "journal" in source_lower:
                query += " AND (source_name LIKE '%Journal%' OR source_name LIKE '%Matin%' OR source_name LIKE '%Économiste%' OR source_name LIKE '%Presse%' OR buyer_normalized IN ('atlantic re', 'laprophan'))"
            elif "atlantic" in source_lower or "scr" in source_lower:
                query += " AND (buyer_normalized LIKE '%atlantic%' OR buyer_normalized LIKE '%scr%' OR source_name LIKE '%Atlantic%')"
            elif "laprophan" in source_lower:
                query += " AND (buyer_normalized LIKE '%laprophan%' OR source_name LIKE '%Laprophan%')"
            elif "pmmp" in source_lower:
                query += " AND (source_name = 'PMMP' OR source_name LIKE '%PMMP%')"
            else:
                query += " AND source_name LIKE ?"
                params.append(f"%{source}%")

        if pipeline_status:
            query += " AND pipeline_status = ?"
            params.append(pipeline_status)

        if min_budget is not None and min_budget > 0:
            query += " AND estimated_budget >= ?"
            params.append(min_budget)

        if search_query:
            words = [w.strip() for w in search_query.split() if len(w.strip()) > 1]
            if not words and search_query.strip():
                words = [search_query.strip()]
            for word in words:
                term = f"%{word}%"
                query += """ AND (
                    title LIKE ? OR 
                    reference LIKE ? OR 
                    buyer_name LIKE ? OR 
                    buyer_normalized LIKE ? OR 
                    summary LIKE ? OR 
                    matched_keywords LIKE ? OR 
                    source_name LIKE ? OR 
                    lots LIKE ? OR 
                    qualifications LIKE ?
                )"""
                params.extend([term, term, term, term, term, term, term, term, term])

        # Dynamic Sorting (Classer par date de publication ou par date de réponse)
        if sort_by == "deadline_asc":
            query += " ORDER BY CASE WHEN deadline IS NULL THEN 1 ELSE 0 END, deadline ASC, publication_date DESC"
        elif sort_by == "deadline_desc":
            query += " ORDER BY CASE WHEN deadline IS NULL THEN 1 ELSE 0 END, deadline DESC, publication_date DESC"
        elif sort_by == "publication_asc":
            query += " ORDER BY CASE WHEN publication_date IS NULL THEN 1 ELSE 0 END, publication_date ASC, deadline ASC"
        elif sort_by == "budget_desc":
            query += " ORDER BY estimated_budget DESC, publication_date DESC"
        elif sort_by == "relevance_desc":
            query += " ORDER BY relevance_score DESC, publication_date DESC"
        else:  # publication_desc (défaut : date de publication décroissante)
            query += " ORDER BY CASE WHEN publication_date IS NULL THEN 1 ELSE 0 END, publication_date DESC, deadline ASC"

        query += " LIMIT ? OFFSET ?"
        params.extend([limit, offset])

        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            rows = cursor.fetchall()
            return [self._row_to_tender(row, conn) for row in rows]

    def get_latest_published_tenders(
        self,
        since: Optional[str] = None,
        limit: int = 5,
        only_tracked: bool = False,
        tracked_ids: Optional[List[str]] = None
    ) -> List[Tender]:
        """Returns active tenders recently indexed or published since a given timestamp (excluding expired)."""
        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with self.get_connection() as conn:
            cursor = conn.cursor()
            conditions = ["(deadline IS NULL OR deadline = '' OR deadline >= ?)"]
            params: list = [now_str]

            if since:
                conditions.append("(first_seen_at > ? OR last_updated_at > ? OR publication_date >= ?)")
                params.extend([since, since, since[:10] if len(since) >= 10 else since])

            if only_tracked:
                tracked_subconds = []
                if tracked_ids:
                    placeholders = ",".join("?" for _ in tracked_ids)
                    tracked_subconds.append(f"id IN ({placeholders})")
                    params.extend(tracked_ids)
                else:
                    tracked_subconds.append("(alert_on_modification = 1 AND relevance_category != 'NOT_RELEVANT' AND relevance_score >= 40)")
                conditions.append(f"({' OR '.join(tracked_subconds)})")
            else:
                # System alert notifications must strictly be relevant cybersecurity opportunities
                conditions.append("(relevance_category != 'NOT_RELEVANT' AND relevance_score >= 40)")

            where_clause = " AND ".join(conditions)
            params.append(limit)
            query = f"SELECT * FROM tenders WHERE {where_clause} ORDER BY first_seen_at DESC, publication_date DESC LIMIT ?"
            cursor.execute(query, tuple(params))
            rows = cursor.fetchall()
            return [self._row_to_tender(r, conn) for r in rows]

    def get_tender_by_id(self, tender_id: str) -> Optional[Tender]:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM tenders WHERE id = ?", (tender_id,))
            row = cursor.fetchone()
            if row:
                return self._row_to_tender(row, conn)
        return None

    def update_pipeline(self, tender_id: str, status: str, notes: str) -> bool:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            now_str = datetime.now().isoformat()
            cursor.execute("""
            UPDATE tenders SET pipeline_status = ?, pipeline_notes = ?, last_updated_at = ?
            WHERE id = ?
            """, (status, notes, now_str, tender_id))
            conn.commit()
            return cursor.rowcount > 0

    def _row_to_tender(self, row: sqlite3.Row, conn: sqlite3.Connection) -> Tender:
        # Load documents
        doc_raw = row["document_links"]
        docs = [DocumentItem(**d) for d in json.loads(doc_raw)] if doc_raw else []

        # Load keywords
        kw_raw = row["matched_keywords"]
        kws = json.loads(kw_raw) if kw_raw else []

        # Load history
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM tender_history WHERE tender_id = ? ORDER BY timestamp DESC", (row["id"],))
        history_rows = cursor.fetchall()
        history = [
            TenderChange(
                timestamp=h["timestamp"],
                field_changed=h["field_changed"],
                old_value=h["old_value"],
                new_value=h["new_value"],
                change_type=h["change_type"]
            )
            for h in history_rows
        ]

        return Tender(
            id=row["id"],
            reference=row["reference"],
            title=row["title"],
            buyer_name=row["buyer_name"],
            buyer_normalized=row["buyer_normalized"] or row["buyer_name"],
            is_priority_buyer=bool(row["is_priority_buyer"]),
            priority_badge=row["priority_badge"],
            procedure_type=row["procedure_type"] or "AOO",
            category=row["category"] or "Services",
            lots=row["lots"],
            publication_date=row["publication_date"],
            deadline=row["deadline"],
            bid_opening_date=row["bid_opening_date"],
            bid_opening_place=row["bid_opening_place"],
            estimated_budget=float(row["estimated_budget"] or 0.0),
            provisional_guarantee=row["provisional_guarantee"],
            qualifications=row["qualifications"],
            agrements=row["agrements"],
            contact=row["contact"],
            source_name=row["source_name"],
            source_url=row["source_url"],
            document_links=docs,
            status=row["status"] or "open",
            relevance_category=row["relevance_category"] or "NOT_RELEVANT",
            relevance_score=int(row["relevance_score"] or 0),
            sub_category=row["sub_category"],
            summary=row["summary"],
            matched_keywords=kws,
            pipeline_status=row["pipeline_status"] or "watching",
            pipeline_notes=row["pipeline_notes"] or "",
            dce_downloaded=bool(row["dce_downloaded"]) if "dce_downloaded" in row.keys() else False,
            dce_downloaded_at=row["dce_downloaded_at"] if "dce_downloaded_at" in row.keys() else None,
            alert_on_modification=bool(row["alert_on_modification"]) if "alert_on_modification" in row.keys() else False,
            history=history,
            first_seen_at=row["first_seen_at"],
            last_updated_at=row["last_updated_at"]
        )

    # Scraper Health
    def save_scraper_health(self, health: ScraperHealth):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
            INSERT INTO scraper_health (
                connector_id, name, url, status, last_run_time, last_success_time,
                items_found_last_run, total_items_indexed, error_message
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(connector_id) DO UPDATE SET
                status = excluded.status,
                last_run_time = excluded.last_run_time,
                last_success_time = excluded.last_success_time,
                items_found_last_run = excluded.items_found_last_run,
                total_items_indexed = excluded.total_items_indexed,
                error_message = excluded.error_message
            """, (
                health.connector_id, health.name, health.url, health.status,
                health.last_run_time, health.last_success_time, health.items_found_last_run,
                health.total_items_indexed, health.error_message
            ))
            conn.commit()

    def get_all_scraper_health(self) -> List[ScraperHealth]:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM scraper_health")
            rows = cursor.fetchall()
            return [
                ScraperHealth(
                    connector_id=r["connector_id"],
                    name=r["name"],
                    url=r["url"],
                    status=r["status"],
                    last_run_time=r["last_run_time"],
                    last_success_time=r["last_success_time"],
                    items_found_last_run=r["items_found_last_run"],
                    total_items_indexed=r["total_items_indexed"],
                    error_message=r["error_message"]
                )
                for r in rows
            ]

    # Watchlist Management
    def get_watchlist(self) -> List[WatchlistBuyer]:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM watchlist ORDER BY name ASC")
            rows = cursor.fetchall()
            return [
                WatchlistBuyer(
                    name=r["name"],
                    normalized_keywords=json.loads(r["normalized_keywords"]),
                    badge_label=r["badge_label"],
                    category=r["category"] or "Établissement Public",
                    notes=r["notes"]
                )
                for r in rows
            ]

    def add_watchlist_buyer(self, buyer: WatchlistBuyer) -> bool:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            try:
                cursor.execute("""
                INSERT INTO watchlist (name, normalized_keywords, badge_label, category, notes)
                VALUES (?, ?, ?, ?, ?)
                """, (buyer.name, json.dumps(buyer.normalized_keywords), buyer.badge_label, buyer.category, buyer.notes))
                conn.commit()
                return True
            except sqlite3.IntegrityError:
                return False

    def delete_watchlist_buyer(self, name: str) -> bool:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM watchlist WHERE name = ?", (name,))
            conn.commit()
            return cursor.rowcount > 0

    # Generic Connectors Management
    def get_generic_connectors(self) -> List[Dict[str, Any]]:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM generic_connectors")
            rows = cursor.fetchall()
            return [dict(r) for r in rows]

    def add_generic_connector(self, data: Dict[str, Any]) -> bool:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
            INSERT OR REPLACE INTO generic_connectors (
                id, name, base_url, listing_url, item_selector, ref_selector,
                title_selector, deadline_selector, budget_selector, doc_link_selector, is_active
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                data["id"], data["name"], data["base_url"], data["listing_url"],
                data["item_selector"], data.get("ref_selector", ""), data["title_selector"],
                data.get("deadline_selector", ""), data.get("budget_selector", ""),
                data.get("doc_link_selector", ""), data.get("is_active", 1)
            ))
            conn.commit()
            return True

    def delete_generic_connector(self, connector_id: str) -> bool:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM generic_connectors WHERE id = ?", (connector_id,))
            conn.commit()
            return cursor.rowcount > 0

    # Alerts Config Management
    def get_alerts_config(self) -> Dict[str, str]:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT key, value FROM alerts_config")
            rows = cursor.fetchall()
            return {r["key"]: r["value"] for r in rows}

    def update_alerts_config(self, config: Dict[str, str]):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            for k, v in config.items():
                cursor.execute("INSERT OR REPLACE INTO alerts_config (key, value) VALUES (?, ?)", (k, v))
            conn.commit()

    # ==================== USER & AUTH MANAGEMENT ====================
    def create_user(
        self,
        email: str,
        full_name: str,
        password: Optional[str] = None,
        role: str = "Consultant Cybersécurité",
        is_admin: bool = False,
        must_change_password: bool = False
    ) -> Tuple[Dict[str, Any], str]:
        """
        Creates a new user for @dpg-cyber.com.
        If password is not provided, generates a secure random password.
        Returns: (user_dict, plain_password)
        """
        email_clean = email.strip().lower()
        if not password:
            generated_suffix = secrets.token_urlsafe(6)
            plain_password = f"DPG-2026-{generated_suffix}"
        else:
            plain_password = password

        pwd_hash, salt = hash_password(plain_password)
        user_id = f"usr_{secrets.token_hex(8)}"
        now_str = datetime.now().isoformat()
        must_change_pwd = 1 if (not password or must_change_password) else 0

        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
            INSERT INTO users (
                id, email, full_name, password_hash, salt, role, is_active, is_admin, must_change_password, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, 1, ?, ?, ?)
            """, (
                user_id, email_clean, full_name.strip(), pwd_hash, salt,
                role.strip(), 1 if is_admin else 0, must_change_pwd, now_str
            ))
            conn.commit()

        user = self.get_user_by_id(user_id)
        return user, plain_password

    def change_user_password(self, user_id: str, new_password: str) -> bool:
        pwd_hash, salt = hash_password(new_password)
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
            UPDATE users SET password_hash = ?, salt = ?, must_change_password = 0 WHERE id = ?
            """, (pwd_hash, salt, user_id))
            conn.commit()
            return cursor.rowcount > 0

    def get_user_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        email_clean = email.strip().lower()
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM users WHERE LOWER(email) = ?", (email_clean,))
            row = cursor.fetchone()
            if row:
                d = dict(row)
                d.pop("password_hash", None)
                d.pop("salt", None)
                return d
            return None

    def get_user_by_id(self, user_id: str) -> Optional[Dict[str, Any]]:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
            row = cursor.fetchone()
            if row:
                d = dict(row)
                d.pop("password_hash", None)
                d.pop("salt", None)
                return d
            return None

    def authenticate_user(self, email_or_username: str, password: str) -> Optional[Dict[str, Any]]:
        """Verifies email/username and password against the database."""
        val = email_or_username.strip().lower()
        with self.get_connection() as conn:
            cursor = conn.cursor()
            if "@" in val:
                cursor.execute("SELECT * FROM users WHERE LOWER(email) = ? AND is_active = 1", (val,))
            elif val == "admin":
                cursor.execute("SELECT * FROM users WHERE (LOWER(email) = 'admin@dpg-cyber.com' OR is_admin = 1) AND is_active = 1 LIMIT 1")
            else:
                # Security fix: Match exact @dpg-cyber.com domain without LIKE wildcards
                clean_name = val.replace("%", "").replace("_", "")
                cursor.execute("SELECT * FROM users WHERE LOWER(email) = ? AND is_active = 1 LIMIT 1", (f"{clean_name}@dpg-cyber.com",))
            row = cursor.fetchone()
            if not row:
                return None
            
            pwd_hash = row["password_hash"]
            salt = row["salt"]
            if verify_password(password, pwd_hash, salt):
                user_id = row["id"]
                cursor.execute("UPDATE users SET last_login = ? WHERE id = ?", (datetime.now().isoformat(), user_id))
                conn.commit()
                d = dict(row)
                d.pop("password_hash", None)
                d.pop("salt", None)
                return d
            return None

    def create_password_reset_token(self, email: str) -> Optional[str]:
        """Creates a secure reset token valid for 24 hours."""
        user = self.get_user_by_email(email)
        if not user:
            return None
        
        token = secrets.token_urlsafe(32)
        expiry = (datetime.now() + timedelta(hours=24)).isoformat()
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
            UPDATE users SET reset_token = ?, reset_token_expiry = ? WHERE id = ?
            """, (token, expiry, user["id"]))
            conn.commit()
        return token

    def verify_and_consume_reset_token(self, token: str, new_password: str) -> bool:
        """Verifies token validity and updates password (enforcing min 8 chars)."""
        if not token or not new_password or len(new_password) < 8:
            return False
        now_str = datetime.now().isoformat()
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
            SELECT * FROM users WHERE reset_token = ? AND reset_token_expiry > ?
            """, (token, now_str))
            row = cursor.fetchone()
            if not row:
                return False
            
            pwd_hash, salt = hash_password(new_password)
            cursor.execute("""
            UPDATE users SET password_hash = ?, salt = ?, reset_token = NULL, reset_token_expiry = NULL WHERE id = ?
            """, (pwd_hash, salt, row["id"]))
            conn.commit()
            return True

    def create_session(self, user_id: str, duration_days: int = 30) -> str:
        token = secrets.token_hex(32)
        now = datetime.now()
        expires = (now + timedelta(days=duration_days)).isoformat()
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
            INSERT INTO user_sessions (session_token, user_id, created_at, expires_at)
            VALUES (?, ?, ?, ?)
            """, (token, user_id, now.isoformat(), expires))
            conn.commit()
        return token

    def get_user_by_session(self, session_token: str) -> Optional[Dict[str, Any]]:
        now_str = datetime.now().isoformat()
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
            SELECT u.* FROM users u
            JOIN user_sessions s ON u.id = s.user_id
            WHERE s.session_token = ? AND s.expires_at > ? AND u.is_active = 1
            """, (session_token, now_str))
            row = cursor.fetchone()
            if row:
                d = dict(row)
                d.pop("password_hash", None)
                d.pop("salt", None)
                return d
            return None

    def delete_session(self, session_token: str):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM user_sessions WHERE session_token = ?", (session_token,))
            conn.commit()

    def list_users(self) -> List[Dict[str, Any]]:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id, email, full_name, role, is_active, is_admin, created_at, last_login FROM users ORDER BY created_at ASC")
            rows = cursor.fetchall()
            return [dict(r) for r in rows]

