from playwright.sync_api import sync_playwright
import time

with sync_playwright() as p:
    browser = p.chromium.launch(headless=False, args=['--no-sandbox','--disable-dev-shm-usage'])
    context = browser.new_context(viewport={'width': 1920, 'height': 1080}, locale='en-IN', timezone_id='Asia/Kolkata')
    page = context.new_page()
    page.goto('https://www.district.in/', wait_until='networkidle', timeout=60000)
    time.sleep(8)
    anchors = page.query_selector_all('a')
    hrefs = []
    for a in anchors:
        href = a.get_attribute('href') or ''
        if 'hyderabad' in href.lower() or 'events' in href.lower() or 'activities' in href.lower():
            hrefs.append(href)
    print('filtered hrefs count', len(hrefs))
    print(hrefs[:50])
    browser.close()
