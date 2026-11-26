"""
Live test runner for Al Barid Bank Connector.
"""
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.connectors.albaridbank import AlBaridBankConnector
from src.classifier.engine import ClassifierEngine

def main():
    print("=== Testing Al Barid Bank Connector Live ===")
    connector = AlBaridBankConnector()
    classifier = ClassifierEngine()

    print("\n--- Health Check ---")
    health = connector.health_check()
    print(f"Status: {health.status}, URL: {health.url}, Error: {health.error_message}")

    print("\n--- Fetching Live Tenders from Al Barid Bank ---")
    tenders = connector.fetch_tenders()
    print(f"Total Tenders Retrieved from ABB: {len(tenders)}")

    for i, t in enumerate(tenders, 1):
        classified = classifier.classify_tender(t)
        print(f"\n[ABB Tender #{i}]")
        print(f"  Reference:       {classified.reference}")
        print(f"  Title:           {classified.title}")
        print(f"  Buyer:           {classified.buyer_name} ({classified.priority_badge})")
        print(f"  Category:        {classified.category}")
        print(f"  Deadline:        {classified.deadline}")
        print(f"  Source URL:      {classified.source_url}")
        print(f"  Cyber Relevance: {classified.relevance_category} (Score: {classified.relevance_score}%) - {classified.sub_category}")
        print(f"  Summary:         {classified.summary}")

if __name__ == '__main__':
    main()
