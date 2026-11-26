"""
Fetch detail page for real consultations: CNSS 1059609 & DGI 1035530.
"""
import httpx
from bs4 import BeautifulSoup
import re

client = httpx.Client(
    verify=False,
    timeout=30.0,
    headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
)

client.get("https://www.marchespublics.gov.ma/pmmp/")

for ref_c, org_a in [("1059609", "o4d"), ("1035530", "g8e"), ("1052345", "a1t")]:
    url = f"https://www.marchespublics.gov.ma/?page=entreprise.EntrepriseDetailsConsultation&refConsultation={ref_c}&orgAcronyme={org_a}"
    r = client.get(url)
    soup = BeautifulSoup(r.text, "html.parser")
    print(f"\n==============================================")
    print(f"[*] Consultation ref={ref_c}, org={org_a}")
    print(f"Status code: {r.status_code}, Length: {len(r.text)}")
    
    # Extract details
    for label in ["Date et heure limite", "Date de mise en ligne", "Caution", "Lieu d'ouverture", "Mode de passation", "Estimation"]:
        match = soup.find(text=re.compile(label, re.I))
        if match:
            parent = match.find_parent("td") or match.find_parent("div") or match.find_parent("tr")
            if parent:
                print(f"  {label} -> {parent.get_text(separator=' ', strip=True)[:100]}")
