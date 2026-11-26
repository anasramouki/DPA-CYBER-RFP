"""
Targeted inspector for:
1. PMMP tender row details
2. Al Barid Bank tender links & details
3. SOREC tender cards & details
"""
import httpx
from bs4 import BeautifulSoup
import re

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36 CyberRFPMaroc/1.0',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Language': 'fr,fr-FR;q=0.9,en;q=0.8'
}

def inspect_pmmp_rows():
    print("--- PMMP ROWS ---")
    client = httpx.Client(verify=False, timeout=35.0, headers=HEADERS)
    client.get('https://www.marchespublics.gov.ma/pmmp/')
    r = client.get('https://www.marchespublics.gov.ma/index.php?page=entreprise.EntrepriseAdvancedSearch&AllCons&En-cours')
    soup = BeautifulSoup(r.text, 'html.parser')
    
    # Let's search for any element containing 'Référence'
    ref_nodes = soup.find_all(text=re.compile(r'Référence\s*:', re.I))
    print(f"Nodes with 'Référence :': {len(ref_nodes)}")
    if ref_nodes:
        parent = ref_nodes[0].parent
        for _ in range(4):
            if parent:
                parent = parent.parent
        if parent:
            print(f"Container tag: {parent.name}, class: {parent.get('class')}")
            print("Snippet:", repr(parent.get_text(separator=' | ', strip=True)[:400]))
            
    # Also find all elements with class containing 'claro' or 'table' or 'line'
    for c in ['bloc', 'panel', 'search-result', 'line', 'consultation']:
        found = soup.find_all(class_=re.compile(c, re.I))
        if found:
            print(f"Class '{c}' found {len(found)} elements")
            for item in found[:2]:
                txt = item.get_text(separator=' ', strip=True)
                if len(txt) > 40:
                    print(f"  class={item.get('class')} -> {txt[:120]}...")

def inspect_abb_rows():
    print("\n--- ABB ROWS & LINKS ---")
    client = httpx.Client(verify=False, timeout=25.0, headers=HEADERS)
    url = "https://fournisseurs.albaridbank.ma/esop/toolkit/opportunity/current/list.si?reset=true&resetstored=true&userAct=changeLangIndex&language=fr_FR"
    r = client.get(url, follow_redirects=True)
    soup = BeautifulSoup(r.text, 'html.parser')
    table = soup.find('table', class_='list-table')
    if table:
        for tr in table.find_all('tr')[1:4]:
            links = tr.find_all('a', href=True)
            cells = [td.get_text(strip=True) for td in tr.find_all('td')]
            print(f"Row cells: {cells}")
            for a in links:
                print(f"  Link: text='{a.get_text(strip=True)}', href='{a.get('href')}', onclick='{a.get('onclick')}'")

def inspect_sorec_cards():
    print("\n--- SOREC CARDS ---")
    client = httpx.Client(verify=False, timeout=25.0, headers=HEADERS)
    url = "https://www.sorec.ma/appels-offres/"
    r = client.get(url, follow_redirects=True)
    soup = BeautifulSoup(r.text, 'html.parser')
    # Let's inspect the main content area
    main = soup.find('main') or soup.find('div', id='content') or soup.find('div', class_=re.compile(r'content|main', re.I))
    if main:
        print("Main found:", main.name, main.get('class'))
        cards = main.find_all('div', class_=re.compile(r'col|card|item|block|row', re.I))
        print(f"Candidate cards in main: {len(cards)}")
        for c in cards[:5]:
            txt = c.get_text(separator=' | ', strip=True)
            if 'AO' in txt or 'Offre' in txt or 'N°' in txt or len(txt) > 30:
                print(f"Card ({c.get('class')}): {txt[:180]}")
                for a in c.find_all('a', href=True):
                    print(f"   Card link: {a.get_text(strip=True)} -> {a.get('href')}")

if __name__ == '__main__':
    inspect_pmmp_rows()
    inspect_abb_rows()
    inspect_sorec_cards()
