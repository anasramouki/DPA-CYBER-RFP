import httpx
from bs4 import BeautifulSoup
import re

url = "https://www.atlanticre.ma"
headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}

try:
    r = httpx.get(url, headers=headers, verify=False, timeout=15)
    soup = BeautifulSoup(r.text, "html.parser")
    links = [a["href"] for a in soup.find_all("a", href=True)]
    print(f"Total links on Atlantic Re: {len(links)}")
    
    proc_links = [l for l in links if any(k in l.lower() for k in ["achat", "appel", "offre", "consultation", "fournisseur", "marche", "actualite", "presse", "news"])]
    print("Relevant links on Atlantic Re:", proc_links[:15])

except Exception as e:
    print(f"Error: {e}")
