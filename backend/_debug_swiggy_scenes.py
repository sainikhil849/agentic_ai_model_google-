from playwright.sync_api import sync_playwright
import time

with sync_playwright() as p:
    browser = p.chromium.launch(headless=False, args=['--no-sandbox','--disable-dev-shm-usage'])
    context = browser.new_context(viewport={'width': 1920, 'height': 1080}, locale='en-IN', timezone_id='Asia/Kolkata')
    page = context.new_page()
    page.goto('https://www.swiggy.com/scenes', wait_until='networkidle', timeout=60000)
    time.sleep(10)
    print('title', page.title(), 'url', page.url)
    anchors = page.query_selector_all('a')
    hrefs = []
    for a in anchors:
        href = a.get_attribute('href') or ''
        if 'scenes' in href.lower() or 'event' in href.lower() or 'hyderabad' in href.lower():
            hrefs.append(href)
    print('candidate hrefs', len(hrefs))
    print(hrefs[:50])
    body = page.inner_text('body')
    for token in ['Hyderabad', 'events', 'ticket', '₹', 'Scene', 'scenes']:
        print(token, body.count(token))
    browser.close()
