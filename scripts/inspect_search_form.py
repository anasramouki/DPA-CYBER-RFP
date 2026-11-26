"""
Inspect PMMP Search Form controls and test real search query.
"""
import httpx
from bs4 import BeautifulSoup

client = httpx.Client(
    verify=False,
    timeout=30.0,
    headers={
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    }
)

client.get("https://www.marchespublics.gov.ma/pmmp/")
r = client.get("https://www.marchespublics.gov.ma/index.php?page=entreprise.EntrepriseAdvancedSearch&searchAnnCons")
soup = BeautifulSoup(r.text, "html.parser")

print("Form action:", soup.find("form").get("action") if soup.find("form") else "No form")

inputs = soup.find_all("input")
print(f"Total inputs: {len(inputs)}")
for inp in inputs:
    name = inp.get("name")
    id_ = inp.get("id")
    type_ = inp.get("type")
    val = inp.get("value", "")
    if name and any(k in name.lower() for k in ["search", "mot", "objet", "prado", "lancer", "btn", "submit"]):
        print(f"Input: name='{name}', id='{id_}', type='{type_}', val='{val[:30]}'")

selects = soup.find_all("select")
for sel in selects:
    name = sel.get("name")
    print(f"Select: name='{name}', options count: {len(sel.find_all('option'))}")
