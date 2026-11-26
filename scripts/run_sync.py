"""
Full Synchronization Runner for CyberRFP Maroc
Runs all connectors against live sources, classifies all tenders, and populates the database.
"""
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.database import Database
from src.classifier.engine import ClassifierEngine
from src.connectors.pmmp import PMMPConnector
from src.connectors.albaridbank import AlBaridBankConnector
from src.connectors.ofppt import OFPPTConnector
from src.connectors.sorec import SORECConnector

def main():
    print("=" * 60)
    print("🚀 CYBERRFP MAROC - FULL INITIAL DATA INGESTION & CLASSIFICATION")
    print("=" * 60)

    db = Database()
    classifier = ClassifierEngine()

    connectors = {
        "PMMP": PMMPConnector(rate_limit_delay=0.5, fetch_details=True),
        "Al Barid Bank": AlBaridBankConnector(rate_limit_delay=0.5, fetch_details=True),
        "OFPPT": OFPPTConnector(),
        "SOREC": SORECConnector()
    }

    total_ingested = 0
    total_cyber = 0

    for name, connector in connectors.items():
        print(f"\n[+] Ingesting from source: {name} ({connector.base_url})...")
        try:
            tenders = connector.fetch_tenders(max_pages=1)
            print(f"    Found {len(tenders)} tenders from {name}")
            db.save_scraper_health(connector.health)

            for t in tenders:
                classified_t = classifier.classify_tender(t)
                is_new, is_updated = db.upsert_tender(classified_t)
                total_ingested += 1
                if classified_t.relevance_category == "CYBERSECURITY":
                    total_cyber += 1
                    badge = f"[{classified_t.priority_badge}]" if classified_t.is_priority_buyer else ""
                    print(f"    🎯 CYBER TENDER: {classified_t.reference} | {classified_t.buyer_name} {badge}")
                    print(f"       Title: {classified_t.title}")
                    print(f"       Sub-category: {classified_t.sub_category} (Score: {classified_t.relevance_score}%)")
                    print(f"       Deadline: {classified_t.deadline} | Budget: {classified_t.estimated_budget:,.0f} DH")

        except Exception as e:
            print(f"    ❌ Error running {name}: {e}")

    print("\n" + "=" * 60)
    print(f"✅ Ingestion Summary: {total_ingested} total tenders indexed, {total_cyber} cybersecurity opportunities identified.")
    print("=" * 60)

if __name__ == '__main__':
    main()
