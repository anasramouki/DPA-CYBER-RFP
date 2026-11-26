"""
Test Advanced Search on PMMP with keywordSearch and lancerRecherche.
"""
import httpx
from bs4 import BeautifulSoup
import re

base_url = "https://www.marchespublics.gov.ma"

def run_test(kw: str):
    print(f"\n[*] Recherche via Advanced Search pour : '{kw}'")
    client = httpx.Client(
        verify=False,
        timeout=35.0,
        headers={
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "fr,fr-FR;q=0.9,en;q=0.8",
        }
    )
    
    # 1. Init session
    client.get(f"{base_url}/pmmp/")
    
    # 2. Get Advanced Search page
    url_search = f"{base_url}/index.php?page=entreprise.EntrepriseAdvancedSearch&searchAnnCons"
    r = client.get(url_search)
    soup = BeautifulSoup(r.text, "html.parser")
    
    page_state = soup.find("input", {"id": "PRADO_PAGESTATE"})["value"]
    
    # 3. Post form with keywordSearch
    form_data = {
        "PRADO_PAGESTATE": page_state,
        "ctl0$CONTENU_PAGE$AdvancedSearch$keywordSearch": kw,
        "ctl0$CONTENU_PAGE$AdvancedSearch$dateMiseEnLigneStart": "",
        "ctl0$CONTENU_PAGE$AdvancedSearch$dateMiseEnLigneEnd": "",
        "ctl0$CONTENU_PAGE$AdvancedSearch$lancerRecherche": "Lancer la recherche"
    }
    
    resp = client.post(url_search, data=form_data)
    soup_res = BeautifulSoup(resp.text, "html.parser")
    
    cards = soup_res.select("div.generalBox")
    print(f"[+] Résultats trouvés : {len(cards)}")
    
    for i, c in enumerate(cards[:5], 1):
        ref_el = c.select_one("span[id*='_referencem']")
        ref = ref_el.text.strip() if ref_el else "N/A"
        
        objet_el = c.select_one("div.p-objet")
        objet = objet_el.text.replace("Objet :", "").strip() if objet_el else ""
        objet = re.sub(r'\s+', ' ', objet)
        
        buyer_el = c.select_one("div.title.p-card")
        buyer = buyer_el.text.replace("Acheteur public :", "").strip() if buyer_el else ""
        buyer = re.sub(r'\s+', ' ', buyer)
        
        estim_el = c.select_one("span.estim-mad, span[id*='_estimationLabel']")
        estim = estim_el.text.strip() if estim_el else ""
        
        link = c.select_one("a[href*='EntrepriseDetailsConsultation']")
        href = link["href"] if link else ""
        
        # DCE link
        dce_link = ""
        m_ref = re.search(r'refConsultation=([0-9]+)', href)
        m_org = re.search(r'orgAcronyme=([a-zA-Z0-9]+)', href)
        if m_ref and m_org:
            dce_link = f"https://www.marchespublics.gov.ma/index.php?page=entreprise.EntrepriseDemandeTelechargementDce&refConsultation={m_ref.group(1)}&orgAcronyme={m_org.group(1)}"
            
        print(f"\n[{i}] Réf : {ref}")
        print(f"    Acheteur : {buyer}")
        print(f"    Objet    : {objet}")
        print(f"    Budget   : {estim}")
        print(f"    Détail   : https://www.marchespublics.gov.ma{href}")
        print(f"    DCE Link : {dce_link}")

if __name__ == "__main__":
    for k in ["sécurité informatique", "DLP", "réseau", "logiciel"]:
        run_test(k)
