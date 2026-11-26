"""
Background Scheduler for CyberRFP Maroc
Schedules:
1. Periodic polite scrapers run (every 3 hours)
2. Daily Digest email at 08:00 (Casablanca Time)
3. Deadline reminders check (J-7, J-3, J-1)
"""
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger

from src.database import Database
from src.alerts.dispatcher import AlertsDispatcher
from src.classifier.engine import ClassifierEngine


class RFPTaskScheduler:
    def __init__(
        self,
        db: Database,
        connectors: Dict[str, Any],
        classifier: ClassifierEngine
    ):
        self.db = db
        self.connectors = connectors
        self.classifier = classifier
        self.scheduler = BackgroundScheduler()

    def start(self):
        """Initializes and starts background scheduled jobs."""
        cfg = self.db.get_alerts_config()
        self.dispatcher = AlertsDispatcher(config=cfg)

        # 1. Periodic polite scraping job (every 3 hours)
        self.scheduler.add_job(
            self.job_sync_all_sources,
            trigger=IntervalTrigger(hours=3),
            id="job_sync_sources",
            name="Scrapers Sync (every 3 hours)",
            replace_existing=True
        )

        # 2. Daily Digest Job at 08:00 Casablanca Time
        self.scheduler.add_job(
            self.job_send_daily_digest,
            trigger=CronTrigger(hour=8, minute=0, timezone="Africa/Casablanca"),
            id="job_daily_digest",
            name="Daily Procurement Digest (08:00 Morocco Time)",
            replace_existing=True
        )

        # 3. Deadline Reminders Check (Daily at 07:30)
        self.scheduler.add_job(
            self.job_check_deadline_reminders,
            trigger=CronTrigger(hour=7, minute=30, timezone="Africa/Casablanca"),
            id="job_deadline_reminders",
            name="Deadline Reminders J-7, J-3, J-1",
            replace_existing=True
        )

        self.scheduler.start()

    def stop(self):
        if self.scheduler.running:
            self.scheduler.shutdown()

    def job_sync_all_sources(self):
        """Scrapes all registered connectors and dispatches alerts for new/updated cyber tenders."""
        cfg = self.db.get_alerts_config()
        dispatcher = AlertsDispatcher(config=cfg)

        for cid, conn in list(self.connectors.items()):
            try:
                tenders = conn.fetch_tenders(max_pages=1)
                for t in tenders:
                    classified_t = self.classifier.classify_tender(t)
                    # Pass alerts_dispatcher so downloaded tenders automatically receive PMMP modification emails
                    is_new, is_updated = self.db.upsert_tender(classified_t, alerts_dispatcher=dispatcher)

                    # Alert on new cyber tender
                    if is_new and classified_t.relevance_category == "CYBERSECURITY":
                        dispatcher.alert_new_tender(classified_t)

                self.db.save_scraper_health(conn.health)
            except Exception as e:
                conn.health.status = "ERROR"
                conn.health.error_message = str(e)
                self.db.save_scraper_health(conn.health)

    def job_send_daily_digest(self):
        """Gathers open cyber tenders and sends 08:00 AM Digest."""
        cfg = self.db.get_alerts_config()
        dispatcher = AlertsDispatcher(config=cfg)
        open_cyber = self.db.get_tenders(category="CYBERSECURITY", limit=50)
        dispatcher.send_daily_digest(open_cyber)

    def job_check_deadline_reminders(self):
        """Evaluates upcoming deadlines and sends alerts for J-7, J-3, J-1 for cyber and tracked tenders."""
        cfg = self.db.get_alerts_config()
        dispatcher = AlertsDispatcher(config=cfg)
        cyber_tenders = self.db.get_tenders(category="CYBERSECURITY", limit=100)
        tracked_tenders = self.db.get_tenders(pipeline_status="watching", limit=100)
        
        # Combine unique tenders to monitor
        all_to_check = {t.id: t for t in (cyber_tenders + tracked_tenders)}.values()
        today = datetime.now().date()

        for t in all_to_check:
            if not t.deadline:
                continue
            try:
                # Format: YYYY-MM-DD HH:MM:SS
                deadline_dt = datetime.strptime(t.deadline.split(" ")[0], "%Y-%m-%d").date()
                days_diff = (deadline_dt - today).days

                if days_diff in [7, 3, 1]:
                    dispatcher.alert_deadline_reminder(t, days_left=days_diff)
            except Exception:
                continue
