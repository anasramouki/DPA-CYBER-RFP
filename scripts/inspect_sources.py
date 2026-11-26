"""
Live inspection script for Moroccan procurement sources:
1. PMMP (Portail Marocain des Marches Publics)
2. Al Barid Bank (fournisseurs + institutional avis de presse)
3. OFPPT (site direct + PMMP coverage)
4. SOREC (site direct + PMMP coverage)
"""
import sys
import re
import json
import httpx
from bs4 import BeautifulSoup

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36 CyberRFPMaroc/1.0 (contact: info@cyberrfp.ma)',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Language': 'fr,fr-FR;q=0.9,en;q=0.8'
}

def inspect_pmmp():
    print("=== 1. INSPECTING PMMP (marchespublics.gov.ma) ===")
    client = httpx.Client(verify=False, timeout=35.0, headers=HEADERS)
    try:
        r0 = client.get('https://www.marchespublics.gov.ma/pmmp/')
        print(f"PMMP home status: {r0.status_code}")
        
        # Test basic search URL
        url = 'https://www.marchespublics.gov.ma/index.php?page=entreprise.EntrepriseAdvancedSearch&AllCons&En-cours'
        r = client.get(url)
        print(f"PMMP En-cours status: {r.status_code}, length: {len(r.text)}")
        soup = BeautifulSoup(r.text, 'html.parser')
        
        # Find all forms
        for form in soup.find_all('form'):
            print(f"Form id={form.get('id')}, name={form.get('name')}, action={form.get('action')}, method={form.get('method')}")
            fields = []
            for inp in form.find_all(['input', 'select', 'textarea']):
                fields.append((inp.get('name'), inp.get('id'), inp.get('type'), inp.get('value')))
            print(f"  Total fields: {len(fields)}")
            # Search for keyword input
            keyword_inputs = [f for f in fields if f[0] and any(k in f[0].lower() for k in ['mot', 'key', 'search', 'objet', 'titre', 'quick'])]
            print(f"  Keyword inputs: {keyword_inputs}")
        
        # Find consultation items or tables
        print("\nSearching for result rows / items...")
        # Common classes in PMMP
        for cls in ['consultation', 'result', 'bloc', 'ligne', 'table', 'claro']:
            matches = soup.find_all(class_=re.compile(cls, re.I))
            if matches:
                print(f"  Class match for '{cls}': {len(matches)} elements")
                
        # Find links with consultation details
        cons_links = soup.find_all('a', href=re.compile(r'consultation|cons', re.I))
        print(f"Consultation links count: {len(cons_links)}")
        for l in cons_links[:8]:
            print(f"  Link: {l.get('href')} | text: {l.get_text(strip=True)[:80]}")
            
        # Try a direct keyword search for "sécurité" or "informatique"
        print("\nTesting PMMP keyword search GET/POST...")
        # Check if quickSearch works
        search_url = 'https://www.marchespublics.gov.ma/index.php?page=entreprise.EntrepriseAdvancedSearch&searchAnnounce&AllCons'
        # Or test GET with parameters
        test_queries = [
            {'page': 'entreprise.EntrepriseAdvancedSearch', 'AllCons': '', 'En-cours': '', 'searchAnnounce': '', 'keyword': 'sécurité'},
            {'page': 'entreprise.EntrepriseAdvancedSearch', 'AllCons': '', 'En-cours': '', 'searchAnnounce': '', 'key': 'sécurité'},
        ]
        
    except Exception as e:
        print(f"PMMP inspection error: {e}")

def inspect_albaridbank():
    print("\n=== 2. INSPECTING AL BARID BANK ===")
    client = httpx.Client(verify=False, timeout=25.0, headers=HEADERS)
    # 2a: Suppliers portal
    try:
        r1 = client.get('https://fournisseurs.albaridbank.ma', follow_redirects=True)
        print(f"Fournisseurs ABB status: {r1.status_code}, final URL: {r1.url}")
        soup1 = BeautifulSoup(r1.text, 'html.parser')
        print(f"Title: {soup1.title.string.strip() if soup1.title else 'None'}")
        # Check if there is a public opportunities/tenders tab or notice link
        links = soup1.find_all('a', href=True)
        print(f"Total links on login page: {len(links)}")
        for l in links:
            txt = l.get_text(strip=True)
            href = l.get('href')
            print(f"  ABB link: {txt} -> {href}")
    except Exception as e:
        print(f"ABB Suppliers error: {e}")

    # 2b: Institutional site avis de presse
    try:
        r2 = client.get('https://www.albaridbank.ma/fr', follow_redirects=True)
        print(f"\nAl Barid Bank institutional status: {r2.status_code}, final URL: {r2.url}")
        soup2 = BeautifulSoup(r2.text, 'html.parser')
        # Search for "appels d'offres", "avis", "achats", "marches", "fournisseurs"
        found_links = []
        for a in soup2.find_all('a', href=True):
            href = a.get('href')
            text = a.get_text(strip=True).lower()
            if any(k in href.lower() or k in text for k in ['appel', 'offre', 'marche', 'avis', 'presse', 'fournisseur', 'aoo', 'consultation']):
                found_links.append((a.get_text(strip=True), href))
        print(f"Institutional procurement links found: {len(found_links)}")
        for txt, href in found_links[:10]:
            print(f"  Link: {txt} -> {href}")
            
        # Also test direct common URLs
        for path in ['/fr/appels-doffres', '/fr/avis-de-presse', '/fr/appels-d-offres', '/appels-doffres', '/fr/publications']:
            test_url = f"https://www.albaridbank.ma{path}"
            r_test = client.get(test_url, follow_redirects=True)
            print(f"  Testing {test_url} -> {r_test.status_code} ({r_test.url})")
    except Exception as e:
        print(f"ABB Institutional error: {e}")

def inspect_sorec():
    print("\n=== 3. INSPECTING SOREC ===")
    client = httpx.Client(verify=False, timeout=25.0, headers=HEADERS)
    try:
        r = client.get('https://www.sorec.ma', follow_redirects=True)
        print(f"SOREC status: {r.status_code}, final URL: {r.url}")
        soup = BeautifulSoup(r.text, 'html.parser')
        found_links = []
        for a in soup.find_all('a', href=True):
            href = a.get('href')
            text = a.get_text(strip=True).lower()
            if any(k in href.lower() or k in text for k in ['appel', 'offre', 'marche', 'fournisseur', 'consultation']):
                found_links.append((a.get_text(strip=True), href))
        print(f"SOREC procurement links: {len(found_links)}")
        for txt, href in found_links[:10]:
            print(f"  SOREC link: {txt} -> {href}")
            
        # Test common paths
        for path in ['/appels-doffres', '/fr/appels-doffres', '/marches-publics', '/rubrique/appels-doffres']:
            test_url = f"https://www.sorec.ma{path}"
            r_test = client.get(test_url, follow_redirects=True)
            print(f"  Testing {test_url} -> {r_test.status_code} ({r_test.url})")
    except Exception as e:
        print(f"SOREC error: {e}")

if __name__ == '__main__':
    inspect_pmmp()
    inspect_albaridbank()
    inspect_sorec()
