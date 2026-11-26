"""
Test runner for PMMP connector against live portal.
"""
import sys
import os
# Ensure root directory is on python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.connectors.pmmp import PMMPConnector

def main():
    print("Initializing PMMPConnector...")
    connector = PMMPConnector(rate_limit_delay=1.0, fetch_details=True)
    
    print("\n--- Testing Health Check ---")
    health = connector.health_check()
    print(f"Health Status: {health.status}, Last Success: {health.last_success_time}, Error: {health.error_message}")
    
    print("\n--- Fetching Live Open Tenders from PMMP ---")
    tenders = connector.fetch_tenders(max_pages=1)
    print(f"Total Tenders Retrieved: {len(tenders)}")
    
    for i, t in enumerate(tenders[:5], 1):
        print(f"\n[Tender #{i}]")
        print(f"  Reference:       {t.reference}")
        print(f"  Procedure:       {t.procedure_type}")
        print(f"  Buyer:           {t.buyer_name}")
        print(f"  Priority Buyer:  {t.is_priority_buyer} ({t.priority_badge})")
        print(f"  Objet:           {t.title}")
        print(f"  Budget:          {t.estimated_budget:,.2f} DH")
        print(f"  Caution:         {t.provisional_guarantee}")
        print(f"  Deadline:        {t.deadline}")
        print(f"  Publication:     {t.publication_date}")
        print(f"  Opening Place:   {t.bid_opening_place}")
        print(f"  Qualifications:  {t.qualifications}")
        print(f"  Contact:         {t.contact}")
        print(f"  Status:          {t.status}")
        print(f"  Source URL:      {t.source_url}")
        print(f"  Documents ({len(t.document_links)}):")
        for doc in t.document_links:
            print(f"    - [{doc.doc_type}] {doc.title} -> {doc.url}")

if __name__ == '__main__':
    main()
