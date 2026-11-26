"""
Find deadline container in detail page.
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

el = soup.find(string=re.compile("remise des plis", re.I))
if el:
    p = el.parent
    for _ in range(3):
        print(f"Parent tag: {p.name}, class: {p.get('class')}, text: {p.get_text(separator=' ', strip=True)[:150]}")
        p = p.parent
