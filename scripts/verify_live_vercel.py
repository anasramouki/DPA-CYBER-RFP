from playwright.sync_api import sync_playwright

def verify():
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={'width': 1440, 'height': 900})
        page.goto('https://dpa-cyber-rfp.vercel.app', wait_until='networkidle')
        screenshot_path = r'C:\Users\Anas Ramouki\.gemini\antigravity\brain\5579530d-cad5-43fe-883f-7e2ca17c6091\vercel_live_v2.png'
        page.screenshot(path=screenshot_path)
        
        export_btn = page.locator('button:has-text("CSV")').count()
        copy_btn = page.locator('button:has-text("Synthèse")').count()
        cards_count = page.locator('.card-modern').count()
        print(f"Export button found: {export_btn > 0}")
        print(f"Copy synthesis button found: {copy_btn > 0}")
        print(f"Rendered modern cards count: {cards_count}")
        
        # Test scrollWidth vs clientWidth
        scroll_width = page.evaluate("() => document.documentElement.scrollWidth")
        client_width = page.evaluate("() => document.documentElement.clientWidth")
        print(f"Scroll width: {scroll_width}, Client width: {client_width} (No horizontal scroll: {scroll_width == client_width})")
        
        browser.close()

if __name__ == "__main__":
    verify()
