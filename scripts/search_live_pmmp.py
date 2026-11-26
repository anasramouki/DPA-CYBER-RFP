"""
Real-time Live PMMP Search & DCE Link Extractor
Queries https://www.marchespublics.gov.ma directly for active IT and Cybersecurity consultations.
"""
import httpx
from bs4 import BeautifulSoup
import re
import urllib.parse
import json

base_url = "https://www.marchespublics.gov.ma"

def search_pmmp(keyword: str):
    print(f"\n==========================================")
    print(f"[*] Recherche en direct sur PMMP pour : '{keyword}'")
    print(f"==========================================")
    
    client = httpx.Client(
        verify=False,
        timeout=30.0,
        headers={
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "fr,fr-FR;q=0.9,en;q=0.8",
        }
    )
    
    # Init cookies
    init_resp = client.get(f"{base_url}/pmmp/")
    
    # 1. First get the search page to grab PRADO_PAGESTATE and form tokens
    search_page = client.get(f"{base_url}/index.php?page=entreprise.EntrepriseAdvancedSearch&AllCons&En-cours")
    soup_page = BeautifulSoup(search_page.text, "html.parser")
    
    page_state = ""
    page_state_input = soup_page.find("input", {"id": "PRADO_PAGESTATE"})
    if page_state_input and page_state_input.get("value"):
        page_state = page_state_input["value"]
        
    # POST quickSearch with keyword
    search_post_url = f"{base_url}/index.php?page=entreprise.EntrepriseAdvancedSearch&AllCons&En-cours"
    post_data = {
        "PRADO_PAGESTATE": page_state,
        "ctl0$menuGaucheEntreprise$quickSearch": keyword,
        "ctl0$menuGaucheEntreprise$imageOk.x": "12",
        "ctl0$menuGaucheEntreprise$imageOk.y": "8",
    }
    
    resp = client.post(search_post_url, data=post_data)
    soup = BeautifulSoup(resp.text, "html.parser")
    
    # Find all generalBox (tender cards)
    cards = soup.select("div.generalBox")
    print(f"[+] Nombre de résultats trouvés : {len(cards)}")
    
    results = []
    for card in cards:
        # Reference
        ref_el = card.select_one("span[id*='_referencem']")
        ref = ref_el.text.strip() if ref_el else "N/A"
        
        # Objet
        objet_el = card.select_one("div.p-objet")
        objet = ""
        if objet_el:
            txt = objet_el.text.strip()
            if "Objet :" in txt:
                objet = txt.split("Objet :", 1)[1].strip()
            else:
                objet = txt
        # Clean multiline whitespace
        objet = re.sub(r'\s+', ' ', objet)
        
        # Buyer
        buyer_el = card.select_one("div.title.p-card")
        buyer = ""
        if buyer_el:
            txt = buyer_el.text.strip()
            if "Acheteur public :" in txt:
                buyer = txt.split("Acheteur public :", 1)[1].strip()
            else:
                buyer = txt
        buyer = re.sub(r'\s+', ' ', buyer)
        
        # Estimation / Budget
        estim_el = card.select_one("span.estim-mad, span[id*='_estimationLabel']")
        estimation = estim_el.text.strip() if estim_el else "Non précisée"
        
        # Deadline
        date_el = card.select_one(".limita.p-card .fa-calendar-o + span")
        time_el = card.select_one(".limita.p-card .fa-clock-o + span")
        deadline = f"{date_el.text.strip() if date_el else ''} {time_el.text.strip() if time_el else ''}".strip()
        
        # Detail & DCE links
        detail_a = card.select_one("a[href*='EntrepriseDetailsConsultation']")
        detail_url = ""
        dce_url = ""
        ref_consultation = ""
        org_acronyme = ""
        
        if detail_a and detail_a.get("href"):
            raw_href = detail_a["href"]
            if raw_href.startswith("/"):
                detail_url = f"{base_url}{raw_href}"
            elif raw_href.startswith("http"):
                detail_url = raw_href
            else:
                detail_url = f"{base_url}/{raw_href}"
                
            # Extract refConsultation and orgAcronyme
            m_ref = re.search(r'refConsultation=([0-9]+)', raw_href)
            m_org = re.search(r'orgAcronyme=([a-zA-Z0-9]+)', raw_href)
            if m_ref:
                ref_consultation = m_ref.group(1)
            if m_org:
                org_acronyme = m_org.group(1)
                
            if ref_consultation and org_acronyme:
                dce_url = f"https://www.marchespublics.gov.ma/index.php?page=entreprise.EntrepriseDemandeTelechargementDce&refConsultation={ref_consultation}&orgAcronyme={org_acronyme}"
                
        results.append({
            "reference": ref,
            "title": objet,
            "buyer": buyer,
            "budget": estimation,
            "deadline": deadline,
            "ref_consultation": ref_consultation,
            "org_acronyme": org_acronyme,
            "detail_url": detail_url,
            "dce_download_url": dce_url
        })
        
        print(f"\n--- AO : {ref} ---")
        print(f"  Acheteur : {buyer[:60]}")
        print(f"  Objet    : {objet[:80]}...")
        print(f"  Budget   : {estimation}")
        print(f"  Délai    : {deadline}")
        print(f"  Détail   : {detail_url}")
        print(f"  Lien DCE : {dce_url}")
        
    return results

if __name__ == "__main__":
    for kw in ["sécurité", "informatique", "CNSS", "réseau"]:
        try:
            res = search_pmmp(kw)
        except Exception as e:
            print(f"Erreur recherche '{kw}': {e}")
