import httpx
from bs4 import BeautifulSoup

url = "https://annonces.lematin.ma/annonce/appels-offres/45-a00-dpar-anp-2026/673053/?support=1"
headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}

r = httpx.get(url, headers=headers, verify=False, timeout=15)
soup = BeautifulSoup(r.text, "html.parser")

imgs = [img["src"] for img in soup.find_all("img", src=True) if "annonce" in img["src"].lower() or "journal" in img["src"].lower() or "upload" in img["src"].lower()]
print("Images found:", imgs)

# Let's also look for text containers
for div in soup.find_all("div"):
    if div.get("id") or (div.get("class") and any("detail" in c or "body" in c or "content" in c for c in div.get("class"))):
        t = div.get_text(strip=True)
        if 20 < len(t) < 500:
            print("Div:", div.get("id"), div.get("class"), "->", t)
