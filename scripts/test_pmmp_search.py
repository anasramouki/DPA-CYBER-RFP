"""
Test PMMP Search with Keywords
"""
import httpx
from bs4 import BeautifulSoup

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36 CyberRFPMaroc/1.0',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Language': 'fr,fr-FR;q=0.9,en;q=0.8'
}

client = httpx.Client(verify=False, timeout=35.0, headers=HEADERS)
# Initialize session
client.get('https://www.marchespublics.gov.ma/pmmp/')

# Test quickSearch POST or GET
# Let's see the form in PMMP:
# ctl0$menuGaucheEntreprise$quickSearch
# or GET with EntrepriseAdvancedSearch parameters
url = 'https://www.marchespublics.gov.ma/index.php?page=entreprise.EntrepriseAdvancedSearch&AllCons&En-cours'
data = {
    'ctl0$menuGaucheEntreprise$quickSearch': 'sécurité',
    'ctl0$menuGaucheEntreprise$imageOk.x': '10',
    'ctl0$menuGaucheEntreprise$imageOk.y': '10',
}
r_post = client.post(url, data=data)
print("POST status:", r_post.status_code, "Length:", len(r_post.text))
soup = BeautifulSoup(r_post.text, 'html.parser')
boxes = soup.find_all('div', class_='generalBox')
print("generalBoxes found after POST quickSearch 'sécurité':", len(boxes))
for b in boxes[:3]:
    ref = b.find(string=lambda t: t and 'Référence' in t)
    obj = b.find(string=lambda t: t and 'Objet' in t)
    buyer = b.find(string=lambda t: t and 'Acheteur' in t)
    print("---")
    print("Snippet:", repr(b.get_text(separator=' | ', strip=True)[:250]))

# Also check GET parameters
r_get = client.get('https://www.marchespublics.gov.ma/index.php?page=entreprise.EntrepriseAdvancedSearch&AllCons&En-cours&keywords=sécurité')
soup_get = BeautifulSoup(r_get.text, 'html.parser')
boxes_get = soup_get.find_all('div', class_='generalBox')
print("\ngeneralBoxes with GET keyword:", len(boxes_get))
