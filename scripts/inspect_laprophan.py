import httpx
from bs4 import BeautifulSoup

url = "https://laprophan.com"
headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}

try:
    r = httpx.get(url, headers=headers, verify=False, timeout=15)
    soup = BeautifulSoup(r.text, "html.parser")
    links = [a["href"] for a in soup.find_all("a", href=True)]
    print(f"Total links on Laprophan: {len(links)}")
    
    proc_links = [l for l in links if any(k in l.lower() for k in ["achat", "appel", "offre", "consultation", "fournisseur", "marche", "actualite", "presse", "news", "contact"])]
    print("Relevant links on Laprophan:", set(proc_links))

except Exception as e:
    print(f"Error: {e}")
