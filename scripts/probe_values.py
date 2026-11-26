"""
Extract values next to labels in detail page.
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
url = "https://www.marchespublics.gov.ma/?page=entreprise.EntrepriseDetailsConsultation&refConsultation=1059609&orgAcronyme=o4d"
r = client.get(url)
soup = BeautifulSoup(r.text, "html.parser")

for label in ["Date et heure limite de remise des plis", "Date de mise en ligne", "Caution provisoire", "Lieu d'ouverture des plis", "Estimation (en Dhs TTC)"]:
    el = soup.find(string=re.compile(label, re.I))
    if el:
        parent = el.find_parent("td") or el.find_parent("th") or el.find_parent("div")
        # Try next sibling
        sibling = parent.find_next_sibling() if parent else None
        print(f"LABEL: {label}")
        print(f"  Parent: {parent.get_text(strip=True) if parent else None}")
        print(f"  Sibling: {sibling.get_text(strip=True) if sibling else None}")
