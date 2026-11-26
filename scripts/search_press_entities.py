import httpx
from bs4 import BeautifulSoup
import urllib.parse

headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}

queries = ["Atlantic Re", "Societe Centrale de Reassurance", "Laprophan"]

for q in queries:
    search_url = f"https://annonces.lematin.ma/annonces/appels-offres/?mot-cle={urllib.parse.quote(q)}"
    try:
        r = httpx.get(search_url, headers=headers, verify=False, timeout=12)
        print(f"Query '{q}' -> Status: {r.status_code}, Length: {len(r.text)}")
        soup = BeautifulSoup(r.text, "html.parser")
        items = soup.find_all("a", href=lambda h: h and "/annonce/" in h)
        print(f"Items found: {len(items)}")
        for it in items[:3]:
            print("  Item:", it.get_text(strip=True)[:100], "->", it.get("href"))
    except Exception as e:
        print(f"Error for {q}: {e}")
