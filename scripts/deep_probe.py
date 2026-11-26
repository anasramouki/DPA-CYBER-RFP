"""
Deep dive probe for:
1. Al Barid Bank public opportunities
2. SOREC appels-offres
3. PMMP consultations table parsing
"""
import httpx
from bs4 import BeautifulSoup
import re

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36 CyberRFPMaroc/1.0',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Language': 'fr,fr-FR;q=0.9,en;q=0.8'
}

def check_abb_public():
    print("=== CHECKING ABB PUBLIC OPPORTUNITIES ===")
    url = "https://fournisseurs.albaridbank.ma/esop/guest/go/public/opportunity/current?locale=fr_FR"
    client = httpx.Client(verify=False, timeout=25.0, headers=HEADERS)
    try:
        r = client.get(url, follow_redirects=True)
        print(f"ABB Public Opp status: {r.status_code}, URL: {r.url}, length: {len(r.text)}")
        soup = BeautifulSoup(r.text, 'html.parser')
        print(f"Title: {soup.title.string.strip() if soup.title else 'None'}")
        tables = soup.find_all('table')
        print(f"Tables found: {len(tables)}")
        for i, t in enumerate(tables):
            rows = t.find_all('tr')
            print(f"Table {i}: id={t.get('id')}, class={t.get('class')}, rows={len(rows)}")
            for r_idx, row in enumerate(rows[:5]):
                cols = [c.get_text(strip=True) for c in row.find_all(['td', 'th'])]
                print(f"  row {r_idx}: {cols}")
    except Exception as e:
        print(f"ABB error: {e}")

def check_abb_espace_fournisseurs():
    print("\n=== CHECKING ABB ESPACE FOURNISSEURS ===")
    url = "https://www.albaridbank.ma/fr/espace-fournisseurs"
    client = httpx.Client(verify=False, timeout=25.0, headers=HEADERS)
    try:
        r = client.get(url, follow_redirects=True)
        print(f"ABB espace-fournisseurs status: {r.status_code}, URL: {r.url}, length: {len(r.text)}")
        soup = BeautifulSoup(r.text, 'html.parser')
        links = soup.find_all('a', href=True)
        for a in links:
            href = a.get('href')
            txt = a.get_text(strip=True)
            if any(k in href.lower() or k in txt.lower() for k in ['pdf', 'avis', 'aoo', 'consultation', 'offre']):
                print(f"  Doc/Notice link: {txt} -> {href}")
    except Exception as e:
        print(f"ABB espace-fournisseurs error: {e}")

def check_sorec_tenders():
    print("\n=== CHECKING SOREC TENDERS ===")
    url = "https://www.sorec.ma/appels-offres/"
    client = httpx.Client(verify=False, timeout=25.0, headers=HEADERS)
    try:
        r = client.get(url, follow_redirects=True)
        print(f"SOREC tenders status: {r.status_code}, URL: {r.url}, length: {len(r.text)}")
        soup = BeautifulSoup(r.text, 'html.parser')
        # Check articles or items
        items = soup.find_all(['article', 'div'], class_=re.compile(r'tender|offre|item|post|card|table', re.I))
        print(f"Candidate items in SOREC: {len(items)}")
        links = soup.find_all('a', href=True)
        pdf_links = [a for a in links if a.get('href').endswith('.pdf') or 'telecharger' in a.get('href').lower()]
        print(f"PDF/Download links in SOREC: {len(pdf_links)}")
        for a in pdf_links[:5]:
            print(f"  PDF link: {a.get_text(strip=True)} -> {a.get('href')}")
        # print first 5 general links
        for a in [l for l in links if 'appel' in l.get('href').lower() or 'offre' in l.get('href').lower()][:5]:
            print(f"  Offer link: {a.get_text(strip=True)} -> {a.get('href')}")
    except Exception as e:
        print(f"SOREC error: {e}")

def check_pmmp_detail():
    print("\n=== CHECKING PMMP DETAIL PARSING ===")
    client = httpx.Client(verify=False, timeout=35.0, headers=HEADERS)
    client.get('https://www.marchespublics.gov.ma/pmmp/')
    r = client.get('https://www.marchespublics.gov.ma/index.php?page=entreprise.EntrepriseAdvancedSearch&AllCons&En-cours')
    soup = BeautifulSoup(r.text, 'html.parser')
    
    # In PMMP, results are in a table or structured repeater
    # Let's search for patterns like 'Référence', 'Objet', 'Acheteur', 'Date limite'
    body_text = soup.get_text()
    for term in ['Référence', 'Acheteur', 'Date limite', 'Caution', 'DCE']:
        found = term.lower() in body_text.lower()
        print(f"Term '{term}' present in PMMP page: {found}")

    # Look for table with headers
    for t in soup.find_all('table'):
        headers = [th.get_text(strip=True) for th in t.find_all('th')]
        if headers:
            print(f"Found table with headers: {headers}")
            rows = t.find_all('tr')
            print(f"  Rows count: {len(rows)}")
            for row in rows[1:4]:
                cols = [td.get_text(separator=' ', strip=True) for td in row.find_all('td')]
                print(f"  Row: {cols[:4]}")
                # Look for links in this row
                for a in row.find_all('a', href=True):
                    print(f"    Link in row: {a.get_text(strip=True)} -> {a.get('href')}")

if __name__ == '__main__':
    check_abb_public()
    check_abb_espace_fournisseurs()
    check_sorec_tenders()
    check_pmmp_detail()
