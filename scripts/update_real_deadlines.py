"""
Script to extract exact real publication dates and response deadline dates for all 54 PMMP tenders
directly from their live consultation details page on https://www.marchespublics.gov.ma.
"""
import sqlite3
import httpx
from bs4 import BeautifulSoup
import re
import os
import sys
import time

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from scripts.harvest_all_real_pmmp import parse_pmmp_date

DB_PATHS = [
    os.path.join(BASE_DIR, "cyberrfp.db"),
    os.path.join(BASE_DIR, "dist", "cyberrfp.db")
]

def update_deadlines():
    conn = sqlite3.connect(DB_PATHS[0])
    cur = conn.cursor()
    cur.execute("SELECT id, reference, source_url FROM tenders")
    tenders = cur.fetchall()
    print(f"[*] Processing {len(tenders)} tenders from database...")

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"
    }

    updates = []
    with httpx.Client(verify=False, headers=headers, timeout=20.0) as client:
        # Establish PMMP session
        client.get("https://www.marchespublics.gov.ma/pmmp/")

        for idx, (t_id, ref, url) in enumerate(tenders, 1):
            if not url or "marchespublics.gov.ma" not in url:
                continue
            try:
                r = client.get(url)
                if r.status_code != 200:
                    print(f"[{idx}/{len(tenders)}] {ref} -> HTTP {r.status_code}")
                    continue
                soup = BeautifulSoup(r.text, "html.parser")
                
                # Deadline (Remise des plis)
                sp_dead = soup.select_one("span[id*='dateHeureLimiteRemisePlis']")
                deadline = parse_pmmp_date(sp_dead.get_text(strip=True)) if sp_dead else ""
                
                # Publication date (Mise en ligne)
                sp_pub = soup.select_one("span[id*='dateMiseEnLigne']")
                pub_date = parse_pmmp_date(sp_pub.get_text(strip=True)) if sp_pub else ""

                if deadline or pub_date:
                    updates.append((t_id, ref, pub_date, deadline))
                    print(f"[{idx}/{len(tenders)}] {ref} -> Pub: {pub_date or 'Keep'} | Deadline: {deadline or 'Keep'}")
                else:
                    print(f"[{idx}/{len(tenders)}] {ref} -> No dates found")

                time.sleep(0.15)
            except Exception as e:
                print(f"[{idx}/{len(tenders)}] {ref} -> Error: {e}")

    print(f"\n[*] Updating {len(updates)} tenders in databases...")
    for db_path in DB_PATHS:
        if not os.path.exists(db_path):
            continue
        c = sqlite3.connect(db_path)
        for t_id, ref, pub_date, deadline in updates:
            if pub_date and deadline:
                c.execute("UPDATE tenders SET publication_date = ?, deadline = ? WHERE id = ?", (pub_date, deadline, t_id))
            elif deadline:
                c.execute("UPDATE tenders SET deadline = ? WHERE id = ?", (deadline, t_id))
            elif pub_date:
                c.execute("UPDATE tenders SET publication_date = ? WHERE id = ?", (pub_date, t_id))
        c.commit()
        c.close()
        print(f"  [✓] Updated {db_path}")

    print("[*] Done!")

if __name__ == "__main__":
    update_deadlines()
