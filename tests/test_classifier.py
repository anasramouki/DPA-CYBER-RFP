"""
Unit Tests for Cybersecurity Classifier Engine
Tests real-world positive and negative Moroccan public procurement titles in FR, AR, EN.
"""
import sys
import os
import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.classifier.rules import classify_text_rules
from src.classifier.engine import ClassifierEngine
from src.models import Tender


def test_positive_soc_siem_french():
    title = "Acquisition, déploiement et maintien en conditions opérationnelles d'une solution SIEM et supervision SOC"
    cat, score, subcat, keywords = classify_text_rules(title)
    assert cat == "CYBERSECURITY"
    assert score >= 70
    assert "SOC & Supervision SIEM" in subcat or "SOC" in subcat
    assert any("siem" in k.lower() or "soc" in k.lower() for k in keywords)


def test_positive_audit_pentest_french():
    title = "Prestation d'audit organisationnel et technique de sécurité des systèmes d'information (SSI) et tests d'intrusion"
    cat, score, subcat, keywords = classify_text_rules(title)
    assert cat == "CYBERSECURITY"
    assert score >= 75
    assert "Audit" in subcat or "Pentest" in subcat or "SSI" in subcat


def test_positive_firewall_waf():
    title = "Fourniture, installation et configuration de boîtiers pare-feu (Next-Gen Firewall) et solution WAF périmétrique"
    cat, score, subcat, keywords = classify_text_rules(title)
    assert cat == "CYBERSECURITY"
    assert score >= 60
    assert "Pare-feu" in subcat or "WAF" in subcat


def test_positive_dnssi_compliance():
    title = "Assistance technique pour la mise en conformité avec la directive nationale de la sécurité (DNSSI) et préparation à l'homologation"
    cat, score, subcat, keywords = classify_text_rules(title)
    assert cat == "CYBERSECURITY"
    assert score >= 60
    assert "DNSSI" in subcat or "Conformité" in subcat or "SSI" in subcat


def test_positive_iam_pam():
    title = "Acquisition d'une solution de gestion des comptes à privilèges (PAM) et authentification multifacteur (MFA)"
    cat, score, subcat, keywords = classify_text_rules(title)
    assert cat == "CYBERSECURITY"
    assert score >= 60
    assert "IAM/PAM" in subcat or "Identités" in subcat


def test_positive_arabic_cyber():
    title = "تقديم خدمات تدقيق الأمن السيبراني واختبار الاختراق لأنظمة المعلومات"
    cat, score, subcat, keywords = classify_text_rules(title)
    assert cat == "CYBERSECURITY"
    assert score >= 60
    assert any("الأمن السيبراني" in k or "اختراق" in k or "تدقيق" in k for k in keywords)


def test_negative_securite_incendie():
    # Must NOT classify as CYBERSECURITY despite containing "sécurité"
    title = "Travaux de mise en conformité des installations de sécurité incendie, extincteurs et systèmes de désenfumage"
    cat, score, subcat, keywords = classify_text_rules(title)
    assert cat == "NOT_RELEVANT"
    assert score < 30


def test_negative_gardiennage():
    title = "Prestations de gardiennage et de surveillance humaine des bâtiments administratifs et locaux annexes"
    cat, score, subcat, keywords = classify_text_rules(title)
    assert cat == "NOT_RELEVANT"
    assert score < 25


def test_negative_securite_routiere():
    title = "Fourniture et pose d'équipements de sécurité routière et signalisation horizontale sur le réseau routier provincial"
    cat, score, subcat, keywords = classify_text_rules(title)
    assert cat == "NOT_RELEVANT"
    assert score < 25


def test_negative_civil_engineering():
    title = "Travaux de mise à niveau de la RP2108 du PK 31+500 au PK 54+500 – Province d’El Kelaa des Sraghna"
    cat, score, subcat, keywords = classify_text_rules(title)
    assert cat == "NOT_RELEVANT"
    assert score == 0


def test_contextual_maybe_storage_backup():
    title = "Acquisition et mise en service d'une baie de stockage SAN et solution logicielle de sauvegarde des données"
    cat, score, subcat, keywords = classify_text_rules(title)
    assert cat in ["MAYBE", "CYBERSECURITY"]
    assert score >= 25


def test_classifier_engine_tender_mutation():
    engine = ClassifierEngine()
    tender = Tender(
        id="test-1",
        reference="AO 2026/01",
        title="Audit de cybersécurité et analyse de vulnérabilités selon la loi 05-20",
        buyer_name="OFPPT",
        source_name="PMMP",
        source_url="https://example.com"
    )
    classified = engine.classify_tender(tender)
    assert classified.relevance_category == "CYBERSECURITY"
    assert classified.relevance_score >= 60
    assert len(classified.matched_keywords) > 0
    assert classified.summary is not None
