"""
Alerts Dispatcher for CyberRFP Maroc
Dispatches Email and Telegram/WhatsApp-compatible Webhook notifications:
1. New cybersecurity tenders
2. Tender corrigenda and postponements
3. Approaching deadline reminders (J-7, J-3, J-1)
4. Daily Digest at 08:00 Morocco Time
"""
import smtplib
import os
import json
import html
import logging
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import httpx

from src.models import Tender, TenderChange

logger = logging.getLogger("cyberrfp.alerts")


class AlertsDispatcher:
    def __init__(self, config: Optional[Dict[str, str]] = None):
        self.config = config or {}
        self.last_error: Optional[str] = None

    def _get_setting(self, key: str, default: str = "") -> str:
        return self.config.get(key) or os.environ.get(key.upper(), default)

    # ==================== DISPATCH CHANNELS ====================

    def send_webhook(self, message_text: str, payload_data: Optional[Dict[str, Any]] = None) -> bool:
        """Sends alert to configured Telegram or WhatsApp/generic webhook."""
        webhook_url = self._get_setting("webhook_url")
        if not webhook_url or "TOKEN" in webhook_url:
            return False

        webhook_type = self._get_setting("webhook_type", "generic").lower()

        try:
            with httpx.Client(timeout=10.0) as client:
                if "telegram.org" in webhook_url or webhook_type == "telegram":
                    # Telegram format
                    data = {
                        "text": message_text,
                        "parse_mode": "Markdown",
                        "disable_web_page_preview": False
                    }
                    client.post(webhook_url, json=data)
                else:
                    # Generic webhook payload (compatible with WhatsApp bridge / Slack)
                    body = {
                        "text": message_text,
                        "timestamp": datetime.now().isoformat(),
                        "tender_data": payload_data or {}
                    }
                    client.post(webhook_url, json=body)
            return True
        except Exception:
            return False

    def send_email(self, subject: str, html_body: str, text_body: str = "") -> bool:
        """Sends email alert via SMTP."""
        recipients_str = self._get_setting("email_recipients")
        if not recipients_str:
            return False
            
        recipients = [r.strip() for r in recipients_str.split(",") if r.strip()]
        if not recipients:
            return False

        smtp_host = self._get_setting("smtp_host", "smtp.gmail.com")
        smtp_port = int(self._get_setting("smtp_port", "587"))
        smtp_user = self._get_setting("smtp_user")
        smtp_password = self._get_setting("smtp_password")

        if not smtp_user or not smtp_password:
            # SMTP credentials not configured
            return False

        try:
            msg = MIMEMultipart("alternative")
            msg["Subject"] = subject
            msg["From"] = f"CyberRFP Maroc <{smtp_user}>"
            msg["To"] = ", ".join(recipients)

            if text_body:
                msg.attach(MIMEText(text_body, "plain", "utf-8"))
            msg.attach(MIMEText(html_body, "html", "utf-8"))

            with smtplib.SMTP(smtp_host, smtp_port, timeout=15) as server:
                server.starttls()
                server.login(smtp_user, smtp_password)
                server.sendmail(smtp_user, recipients, msg.as_string())
            self.last_error = None
            return True
        except Exception as e:
            self.last_error = str(e)
            logger.warning(f"SMTP send_email failed: {e}")
            return False

    def send_email_to(self, to_email: str, subject: str, html_body: str, text_body: str = "") -> bool:
        """Sends an email directly to an individual recipient (e.g. for registration, credentials, password reset)."""
        smtp_host = self._get_setting("smtp_host", "smtp.gmail.com")
        smtp_port = int(self._get_setting("smtp_port", "587"))
        smtp_user = self._get_setting("smtp_user")
        smtp_password = self._get_setting("smtp_password")

        if not smtp_user or not smtp_password:
            self.last_error = "Identifiants SMTP non configurés."
            return False

        try:
            msg = MIMEMultipart("alternative")
            msg["Subject"] = subject
            msg["From"] = f"CyberRFP Maroc - DPA <{smtp_user}>"
            msg["To"] = to_email

            if text_body:
                msg.attach(MIMEText(text_body, "plain", "utf-8"))
            msg.attach(MIMEText(html_body, "html", "utf-8"))

            with smtplib.SMTP(smtp_host, smtp_port, timeout=15) as server:
                server.starttls()
                server.login(smtp_user, smtp_password)
                server.sendmail(smtp_user, [to_email], msg.as_string())
            self.last_error = None
            return True
        except Exception as e:
            self.last_error = str(e)
            logger.warning(f"SMTP send_email_to ({to_email}) failed: {e}")
            return False

    def send_user_welcome_email(self, to_email: str, full_name: str, password: str, login_url: str = "http://localhost:8000/login") -> bool:
        """Sends welcome credentials to newly registered team member @dpg-cyber.com."""
        safe_full_name = html.escape(full_name)
        safe_email = html.escape(to_email)
        safe_password = html.escape(password)
        safe_login_url = html.escape(login_url)

        subject = "Vos identifiants d'accès CyberRFP Maroc — DataProtech Group"
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <body style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; background-color: #0f172a; color: #f8fafc; padding: 24px; margin: 0;">
          <div style="max-width: 600px; margin: 0 auto; background: #1e293b; border: 1px solid #334155; border-radius: 16px; overflow: hidden; box-shadow: 0 10px 25px rgba(0,0,0,0.4);">
            <div style="background: linear-gradient(135deg, #f97316 0%, #ea580c 100%); padding: 24px; text-align: center;">
              <h1 style="color: white; margin: 0; font-size: 20px; font-weight: 800; letter-spacing: 0.5px;">CYBERRFP MAROC</h1>
              <p style="color: rgba(255,255,255,0.9); margin: 4px 0 0; font-size: 13px;">DataProtech Group · Veille Stratégique des Marchés Publics</p>
            </div>
            <div style="padding: 28px; line-height: 1.6; font-size: 14px; color: #cbd5e1;">
              <p style="margin-top: 0;">Bonjour <strong style="color: #ffffff;">{safe_full_name}</strong>,</p>
              <p>Bienvenue sur la plateforme <strong>CyberRFP Maroc</strong>. Votre compte d'accès réservé aux équipes DataProtech a été créé avec succès pour votre adresse professionnelle :</p>
              
              <div style="background: #0f172a; border: 1px solid #334155; border-radius: 12px; padding: 16px; margin: 20px 0;">
                <table style="width: 100%; border-collapse: collapse; font-size: 13px;">
                  <tr>
                    <td style="color: #94a3b8; padding: 6px 0; width: 140px;">Identifiant / Email :</td>
                    <td style="color: #38bdf8; font-weight: bold; padding: 6px 0;">{safe_email}</td>
                  </tr>
                  <tr>
                    <td style="color: #94a3b8; padding: 6px 0;">Mot de passe temporaire :</td>
                    <td style="color: #fbbf24; font-weight: bold; font-family: monospace; font-size: 15px; padding: 6px 0;">{safe_password}</td>
                  </tr>
                </table>
              </div>

              <div style="background: rgba(56, 189, 248, 0.1); border-left: 4px solid #38bdf8; padding: 12px 16px; border-radius: 4px; margin-bottom: 24px;">
                <p style="margin: 0; font-size: 13px; color: #bae6fd;">
                  🔒 <strong>Sécurité renforcée :</strong> Lors de votre première connexion avec ce mot de passe temporaire, l'application vous invitera automatiquement à définir votre nouveau mot de passe personnel définitif.
                </p>
              </div>

              <div style="text-align: center; margin: 28px 0;">
                <a href="{safe_login_url}" style="background: #f97316; color: #ffffff; padding: 12px 28px; border-radius: 8px; text-decoration: none; font-weight: bold; font-size: 14px; display: inline-block;">Accéder à la Plateforme ↗</a>
              </div>

              <p style="font-size: 12px; color: #94a3b8; border-top: 1px solid #334155; padding-top: 16px; margin-bottom: 0;">
                ⚠️ <em>Cet email contient des informations confidentielles destinées exclusivement aux collaborateurs de DataProtech Group (@dpg-cyber.com). Vous pouvez modifier votre mot de passe à tout moment depuis la plateforme.</em>
              </p>
            </div>
          </div>
        </body>
        </html>
        """
        text = f"Bonjour {full_name},\n\nVos identifiants CyberRFP Maroc :\nEmail: {to_email}\nMot de passe: {password}\n\nConnexion : {login_url}"
        return self.send_email_to(to_email, subject, html_content, text)

    def send_password_reset_email(self, to_email: str, full_name: str, reset_url: str) -> bool:
        """Sends password reset link to team member @dpg-cyber.com."""
        safe_full_name = html.escape(full_name)
        safe_email = html.escape(to_email)
        safe_reset_url = html.escape(reset_url)

        subject = "Réinitialisation de votre mot de passe — CyberRFP Maroc"
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <body style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; background-color: #0f172a; color: #f8fafc; padding: 24px; margin: 0;">
          <div style="max-width: 600px; margin: 0 auto; background: #1e293b; border: 1px solid #334155; border-radius: 16px; overflow: hidden; box-shadow: 0 10px 25px rgba(0,0,0,0.4);">
            <div style="background: linear-gradient(135deg, #f97316 0%, #ea580c 100%); padding: 24px; text-align: center;">
              <h1 style="color: white; margin: 0; font-size: 20px; font-weight: 800; letter-spacing: 0.5px;">CYBERRFP MAROC</h1>
              <p style="color: rgba(255,255,255,0.9); margin: 4px 0 0; font-size: 13px;">DataProtech Group · Sécurité & Veille Stratégique</p>
            </div>
            <div style="padding: 28px; line-height: 1.6; font-size: 14px; color: #cbd5e1;">
              <p style="margin-top: 0;">Bonjour <strong style="color: #ffffff;">{safe_full_name}</strong>,</p>
              <p>Une demande de réinitialisation de mot de passe a été émise pour votre compte <strong>{safe_email}</strong> sur la plateforme CyberRFP Maroc.</p>
              
              <div style="text-align: center; margin: 28px 0;">
                <a href="{safe_reset_url}" style="background: #0284c7; color: #ffffff; padding: 12px 28px; border-radius: 8px; text-decoration: none; font-weight: bold; font-size: 14px; display: inline-block;">Définir mon Nouveau Mot de Passe ↗</a>
              </div>

              <p style="font-size: 12px; color: #94a3b8;">
                Si le bouton ci-dessus ne fonctionne pas, copiez et collez l'adresse suivante dans votre navigateur :<br>
                <a href="{safe_reset_url}" style="color: #38bdf8; word-break: break-all;">{safe_reset_url}</a>
              </p>

              <p style="font-size: 12px; color: #64748b; border-top: 1px solid #334155; padding-top: 16px; margin-bottom: 0;">
                Ce lien est sécurisé et valable pendant 24 heures. Si vous n'êtes pas à l'origine de cette demande, vous pouvez ignorer cet e-mail.
              </p>
            </div>
          </div>
        </body>
        </html>
        """
        text = f"Bonjour {full_name},\n\nPour réinitialiser votre mot de passe CyberRFP Maroc, cliquez sur ce lien (valable 24h) :\n{reset_url}"
        return self.send_email_to(to_email, subject, html_content, text)

    # ==================== EVENT TRIGGERS ====================

    def alert_new_tender(self, tender: Tender):
        """Triggered immediately when a relevant cybersecurity tender is detected."""
        badge = f" ⭐ [{tender.priority_badge}]" if tender.is_priority_buyer else ""
        budget_str = f"{tender.estimated_budget:,.2f} DH" if tender.estimated_budget > 0 else "Non estimé"

        # 1. Telegram / Webhook Markdown Message
        tg_text = (
            f"🚨 *NOUVEL APPEL D'OFFRES CYBERSÉCURITÉ* {badge}\n\n"
            f"📋 *Réf :* `{tender.reference}` ({tender.procedure_type})\n"
            f"🏢 *Acheteur :* {tender.buyer_name}\n"
            f"🎯 *Sous-domaine :* {tender.sub_category} (Score : {tender.relevance_score}%)\n"
            f"📝 *Objet :* {tender.title}\n"
            f"💰 *Budget Estimatif :* {budget_str}\n"
            f"🏦 *Caution Provisoire :* {tender.provisional_guarantee or 'S/O'}\n"
            f"⏳ *Date Limite :* *{tender.deadline or 'Non précisée'}*\n"
            f"📌 *Source :* {tender.source_name}\n\n"
            f"🔗 [Accéder à l'avis officiel]({tender.source_url})"
        )
        self.send_webhook(tg_text, tender.model_dump())

        # 2. HTML Email (escaped against HTML injection)
        safe_ref = html.escape(str(tender.reference))
        safe_proc = html.escape(str(tender.procedure_type))
        safe_title = html.escape(str(tender.title))
        safe_buyer = html.escape(str(tender.buyer_name))
        safe_sub = html.escape(str(tender.sub_category))
        safe_caution = html.escape(str(tender.provisional_guarantee or "Non spécifiée"))
        safe_deadline = html.escape(str(tender.deadline or "Non précisée"))
        safe_summary = html.escape(str(tender.summary or ""))
        safe_url = html.escape(str(tender.source_url or "#"), quote=True)

        subject = f"[CyberRFP Maroc] Nouvel AO Cybersécurité : {tender.reference} - {tender.buyer_name}"
        html_body = f"""
        <div style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; max-width: 650px; margin: 0 auto; background: #0f172a; color: #f8fafc; padding: 24px; border-radius: 12px; border: 1px solid #1e293b;">
          <div style="display: flex; align-items: center; margin-bottom: 20px;">
            <h2 style="color: #10b981; margin: 0; font-size: 20px;">🛡️ CyberRFP Maroc - Alerte Nouvelle Opportunité</h2>
          </div>
          <div style="background: #1e293b; padding: 16px; border-radius: 8px; margin-bottom: 20px; border-left: 4px solid #10b981;">
            <p style="margin: 0 0 8px 0; font-size: 14px; font-weight: bold; color: #38bdf8;">{safe_ref} - {safe_proc}</p>
            <h3 style="margin: 0 0 12px 0; font-size: 16px; color: #ffffff;">{safe_title}</h3>
            <p style="margin: 0; font-size: 13px; color: #94a3b8;">Acheteur public : <strong style="color: #f1f5f9;">{safe_buyer}</strong></p>
          </div>
          <table style="width: 100%; border-collapse: collapse; margin-bottom: 20px; font-size: 13px;">
            <tr>
              <td style="padding: 8px; border-bottom: 1px solid #334155; color: #94a3b8;">Sous-catégorie :</td>
              <td style="padding: 8px; border-bottom: 1px solid #334155; color: #10b981; font-weight: bold;">{safe_sub} (Score : {tender.relevance_score}%)</td>
            </tr>
            <tr>
              <td style="padding: 8px; border-bottom: 1px solid #334155; color: #94a3b8;">Budget Estimé :</td>
              <td style="padding: 8px; border-bottom: 1px solid #334155; color: #f8fafc;">{html.escape(budget_str)}</td>
            </tr>
            <tr>
              <td style="padding: 8px; border-bottom: 1px solid #334155; color: #94a3b8;">Caution Provisoire :</td>
              <td style="padding: 8px; border-bottom: 1px solid #334155; color: #f59e0b; font-weight: bold;">{safe_caution}</td>
            </tr>
            <tr>
              <td style="padding: 8px; border-bottom: 1px solid #334155; color: #94a3b8;">Date Limite de Dépôt :</td>
              <td style="padding: 8px; border-bottom: 1px solid #334155; color: #f43f5e; font-weight: bold;">{safe_deadline}</td>
            </tr>
          </table>
          <p style="font-size: 13px; color: #cbd5e1; background: #0b1120; padding: 12px; border-radius: 6px;">
            <strong>Synthèse de besoin :</strong> {safe_summary}
          </p>
          <div style="text-align: center; margin-top: 24px;">
            <a href="{safe_url}" style="background: #10b981; color: #ffffff; padding: 10px 20px; text-decoration: none; border-radius: 6px; font-size: 13px; font-weight: bold;">Consulter l'Avis Officiel & Télécharger DCE</a>
          </div>
        </div>
        """
        self.send_email(subject, html_body, tg_text)

    def alert_tender_change(self, tender: Tender, change: TenderChange):
        """Triggered when a deadline is postponed or corrigendum is detected."""
        icon = "⏳ REPORT DE DATE LIMITE" if change.change_type == "postponement" else "⚠️ RECTIFICATIF / CORRIGENDUM"
        tg_text = (
            f"{icon}\n\n"
            f"📋 *Réf :* `{tender.reference}`\n"
            f"🏢 *Acheteur :* {tender.buyer_name}\n"
            f"📝 *Objet :* {tender.title}\n"
            f"🔄 *Champ Modifié :* {change.field_changed}\n"
            f"❌ *Ancienne Valeur :* {change.old_value}\n"
            f"✅ *Nouvelle Valeur :* *{change.new_value}*\n\n"
            f"🔗 [Voir l'avis à jour]({tender.source_url})"
        )
        self.send_webhook(tg_text, {"tender": tender.model_dump(), "change": change.model_dump()})

    def alert_deadline_reminder(self, tender: Tender, days_left: int):
        """Triggered at J-7, J-3, and J-1 before submission deadline."""
        urgency = "🚨 DERNIER JOUR (J-1)" if days_left == 1 else (f"⚠️ RAPPEL J-{days_left}" if days_left <= 3 else f"ℹ️ ÉCHÉANCE J-{days_left}")
        tg_text = (
            f"{urgency} : Dépôt d'offre imminent !\n\n"
            f"📋 *Réf :* `{tender.reference}`\n"
            f"🏢 *Acheteur :* {tender.buyer_name}\n"
            f"📝 *Objet :* {tender.title}\n"
            f"⏰ *Date Limite :* *{tender.deadline}*\n"
            f"💼 *Statut Pipeline :* {tender.pipeline_status.upper()}\n\n"
            f"🔗 [Accéder au dossier]({tender.source_url})"
        )
        self.send_webhook(tg_text, tender.model_dump())

    def send_daily_digest(self, open_cyber_tenders: List[Tender]):
        """Dispatches the Daily 08:00 AM Procurement Digest."""
        if not open_cyber_tenders:
            return

        date_str = datetime.now().strftime("%d/%m/%Y")
        subject = f"[CyberRFP Maroc] Digest Quotidien des Marchés Cybersécurité - {date_str} ({len(open_cyber_tenders)} AO)"

        items_html = ""
        for t in open_cyber_tenders[:15]:
            budget_str = f"{t.estimated_budget:,.0f} DH" if t.estimated_budget > 0 else "-"
            priority_tag = "<span style='background:#b45309;color:#fff;padding:2px 6px;border-radius:4px;font-size:10px;'>PRIORITAIRE</span>" if t.is_priority_buyer else ""
            items_html += f"""
            <tr style="border-bottom: 1px solid #1e293b;">
              <td style="padding: 10px; font-family: monospace; color: #34d399; font-weight: bold;">{html.escape(str(t.reference))}</td>
              <td style="padding: 10px; color: #f8fafc;">
                <strong>{html.escape(str(t.title))}</strong><br>
                <span style="color: #94a3b8; font-size: 11px;">{html.escape(str(t.buyer_name))} {priority_tag}</span>
              </td>
              <td style="padding: 10px; color: #38bdf8; font-size: 11px;">{html.escape(str(t.sub_category))}</td>
              <td style="padding: 10px; color: #f59e0b; font-weight: bold; font-size: 11px;">{html.escape(str(t.deadline or 'S/O'))}</td>
              <td style="padding: 10px; color: #f1f5f9; font-size: 11px;">{html.escape(budget_str)}</td>
              <td style="padding: 10px; text-align: right;">
                <a href="{html.escape(str(t.source_url or '#'), quote=True)}" style="color: #10b981; text-decoration: none; font-weight: bold; font-size: 11px;">Ouvrir</a>
              </td>
            </tr>
            """

        html_body = f"""
        <div style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; max-width: 800px; margin: 0 auto; background: #0f172a; color: #f8fafc; padding: 24px; border-radius: 12px;">
          <h2 style="color: #10b981; margin: 0 0 6px 0;">🛡️ CyberRFP Maroc - Digest Quotidien à 08:00</h2>
          <p style="margin: 0 0 20px 0; font-size: 13px; color: #94a3b8;">Synthèse des opportunités ouvertes en cybersécurité au Maroc pour le {date_str}.</p>
          <table style="width: 100%; border-collapse: collapse; font-size: 12px; background: #0b1120; border-radius: 8px;">
            <thead>
              <tr style="background: #1e293b; color: #94a3b8; text-align: left; font-size: 11px; text-transform: uppercase;">
                <th style="padding: 10px;">Réf</th>
                <th style="padding: 10px;">Objet & Acheteur</th>
                <th style="padding: 10px;">Sous-domaine</th>
                <th style="padding: 10px;">Délai</th>
                <th style="padding: 10px;">Budget</th>
                <th style="padding: 10px; text-align: right;">Action</th>
              </tr>
            </thead>
            <tbody>
              {items_html}
            </tbody>
          </table>
        </div>
        """

        tg_summary = f"📰 *DIGEST QUOTIDIEN CYBERRFP MAROC ({date_str})*\n\n"
        tg_summary += f"📊 *{len(open_cyber_tenders)} opportunités actives de cybersécurité répertoriées.*\n\n"
        for i, t in enumerate(open_cyber_tenders[:6], 1):
            tg_summary += f"{i}. `{t.reference}` - *{t.buyer_name}* (Délai: {t.deadline or 'S/O'})\n_{t.title[:65]}..._\n\n"

        self.send_email(subject, html_body, tg_summary)
        self.send_webhook(tg_summary)

    # ==================== OFFICIAL PMMP / TGR NOTIFICATIONS ====================

    def format_pmmp_official_email(
        self,
        tender: Tender,
        recipient_name: str = "John Doe",
        event_type: str = "consultation"
    ) -> Tuple[str, str, str]:
        """
        Formats an email identically to the official PMMP / TGR notification:
        Subject: Avertissement - Modification de consultation (or Consultation / Téléchargement DCE)
        Sender: MPE - PORTAIL MAROCAIN DES MARCHES PUBLICS <noreply-marchespublics@tgr.gov.ma>
        """
        if event_type == "modification" or tender.status in ["amended", "postponed"]:
            subject = f"Avertissement - Modification de consultation"
        elif event_type == "download":
            subject = f"Avertissement - Téléchargement DCE & Consultation - {tender.reference}"
        else:
            subject = f"Avertissement - Consultation enregistrée - {tender.reference}"

        # Clean publication date format: DD/MM/YYYY HH:MM
        pub_date_display = tender.publication_date or datetime.now().strftime("%d/%m/%Y %H:%M")
        if "-" in pub_date_display and len(pub_date_display) >= 16:
            try:
                dt = datetime.fromisoformat(pub_date_display)
                pub_date_display = dt.strftime("%d/%m/%Y %H:%M")
            except Exception:
                pass

        # Clean deadline format: DD/MM/YYYY HH:MM
        deadline_display = tender.deadline or "Non précisée"
        if "-" in deadline_display and len(deadline_display) >= 16:
            try:
                dt = datetime.fromisoformat(deadline_display)
                deadline_display = dt.strftime("%d/%m/%Y %H:%M")
            except Exception:
                pass

        # Direct Portal URL
        portal_url = tender.source_url
        if not portal_url or "marchespublics.gov.ma" not in portal_url:
            portal_url = f"https://www.marchespublics.gov.ma/index.php?page=entreprise.EntrepriseAdvancedSearch&keyword={tender.reference}"

        # HTML-escaped variables for safe rendering
        safe_recipient_name = html.escape(recipient_name)
        safe_title = html.escape(tender.title)
        safe_reference = html.escape(tender.reference)
        safe_procedure = html.escape(tender.procedure_type or "Appel d'offres ouvert")
        safe_pub_date = html.escape(pub_date_display)
        safe_deadline = html.escape(deadline_display)
        safe_buyer = html.escape(tender.buyer_name)
        safe_portal_url = html.escape(portal_url)

        # Exact plain text reproduction matching the official notification email
        plain_text = f"""Bonjour,
Un message vous est envoyé concernant la consultation présentée ci-dessous :

Objet de la consultation : {tender.title}
Référence consultation : {tender.reference}
Mode de passation : {tender.procedure_type or "Appel d'offres ouvert"}
Date de mise en ligne : {pub_date_display}
Date et heure limite de remise des plis : {deadline_display}
Le contenu du message qui vous est destiné est accessible à l'adresse suivante :

{portal_url}

Merci de votre intérêt pour cette consultation.
La plate-forme de dématérialisation des marchés publics"""

        html_body = f"""
<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <style>
    body {{
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Arial, sans-serif;
      line-height: 1.5;
      color: #1e293b;
      margin: 0;
      padding: 16px;
      background-color: #f1f5f9;
    }}
    .email-container {{
      max-width: 650px;
      margin: 0 auto;
      background: #ffffff;
      border: 1px solid #cbd5e1;
      border-radius: 6px;
      overflow: hidden;
      box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05);
    }}
    .security-banner {{
      background-color: #fef3c7;
      border-bottom: 2px solid #f59e0b;
      padding: 10px 14px;
      font-size: 11px;
      color: #92400e;
      font-weight: 500;
    }}
    .pmmp-header {{
      background-color: #006039;
      color: #ffffff;
      padding: 14px 18px;
    }}
    .email-body {{
      padding: 24px;
      font-size: 13px;
      color: #334155;
    }}
    .field-label {{
      font-weight: bold;
      color: #0f172a;
    }}
    .field-row {{
      margin-bottom: 10px;
    }}
    .link-box {{
      margin: 20px 0;
      padding: 12px;
      background: #f8fafc;
      border: 1px solid #e2e8f0;
      border-radius: 4px;
      word-break: break-all;
    }}
    .link-box a {{
      color: #0284c7;
      text-decoration: underline;
      font-family: monospace;
      font-size: 12px;
    }}
    .portal-footer {{
      margin-top: 24px;
      padding-top: 16px;
      border-top: 1px solid #e2e8f0;
      font-size: 12px;
      color: #64748b;
    }}
    .action-btn {{
      display: inline-block;
      background-color: #006039;
      color: #ffffff !important;
      padding: 9px 18px;
      border-radius: 4px;
      text-decoration: none !important;
      font-weight: bold;
      font-size: 12px;
      margin-top: 8px;
    }}
  </style>
</head>
<body>
  <div class="email-container">
    <div class="security-banner">
      <strong>CAUTION:</strong> This email originated from outside the DataProtech Group organisation. Do not click links or open attachments unless you recognise the sender and know the content is safe.
    </div>

    <div class="pmmp-header">
      <div style="font-size: 11px; text-transform: uppercase; letter-spacing: 0.05em; color: #fde68a;">Royaume du Maroc — Trésorerie Générale du Royaume</div>
      <div style="font-size: 15px; font-weight: bold;">PORTAIL MAROCAIN DES MARCHÉS PUBLICS (PMMP)</div>
      <div style="font-size: 11px; color: #d1fae5; margin-top: 2px;">Entreprise : DPA (ICE: 003102490000030) | Session Dématérialisée Active</div>
    </div>

    <div class="email-body">
      <p style="margin-top: 0;">Bonjour <strong>{safe_recipient_name}</strong>,</p>
      <p>Un message vous est envoyé concernant la consultation présentée ci-dessous :</p>

      <div class="field-row">
        <span class="field-label">Objet de la consultation :</span> {safe_title}
      </div>
      <div class="field-row">
        <span class="field-label">Référence consultation :</span> <code style="background:#f1f5f9; padding:2px 6px; border-radius:3px; color:#006039; font-weight:bold;">{safe_reference}</code>
      </div>
      <div class="field-row">
        <span class="field-label">Mode de passation :</span> {safe_procedure}
      </div>
      <div class="field-row">
        <span class="field-label">Date de mise en ligne :</span> {safe_pub_date}
      </div>
      <div class="field-row">
        <span class="field-label">Date et heure limite de remise des plis :</span> <strong style="color:#b91c1c;">{safe_deadline}</strong>
      </div>
      <div class="field-row">
        <span class="field-label">Acheteur public :</span> {safe_buyer}
      </div>

      <p style="margin-top: 18px;">Le contenu du message qui vous est destiné est accessible à l'adresse suivante :</p>

      <div class="link-box">
        <a href="{safe_portal_url}" target="_blank">{safe_portal_url}</a>
      </div>

      <div>
        <a href="{safe_portal_url}" class="action-btn" target="_blank">Consulter directement sur le Portail des Marchés Publics</a>
      </div>

      <div class="portal-footer">
        <p style="margin: 0 0 4px 0;">Merci de votre intérêt pour cette consultation.</p>
        <p style="margin: 0; font-weight: bold; color: #006039;">La plate-forme de dématérialisation des marchés publics</p>
      </div>
    </div>
  </div>
</body>
</html>
        """
        return subject, html_body, plain_text

    def send_pmmp_official_alert(
        self,
        tender: Tender,
        recipient_email: Optional[str] = None,
        recipient_name: str = "John Doe",
        event_type: str = "consultation"
    ) -> Dict[str, Any]:
        """
        Sends the official PMMP alert email matching the user's TGR notification format.
        """
        recipients = [recipient_email] if recipient_email else [
            r.strip() for r in (self._get_setting("email_recipients") or "john.doe@dpg-cyber.com").split(",") if r.strip()
        ]
        
        subject, html, plain_text = self.format_pmmp_official_email(
            tender=tender,
            recipient_name=recipient_name,
            event_type=event_type
        )
        
        sent = False
        smtp_user = self._get_setting("smtp_user")
        if smtp_user:
            try:
                sent = self.send_email(subject, html, plain_text)
            except Exception:
                sent = False
                
        return {
            "status": "sent" if sent else "ready",
            "subject": subject,
            "sender": "MPE - PORTAIL MAROCAIN DES MARCHES PUBLICS <noreply-marchespublics@tgr.gov.ma>",
            "recipients": recipients,
            "plain_text": plain_text,
            "html": html,
            "portal_url": tender.source_url
        }
