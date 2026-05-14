from playwright.sync_api import sync_playwright
import time

with sync_playwright() as p:
    browser = p.chromium.launch(headless=False, args=['--no-sandbox','--disable-dev-shm-usage'])
    context = browser.new_context(viewport={'width': 1920, 'height': 1080}, locale='en-IN', timezone_id='Asia/Kolkata')
    page = context.new_page()
    page.goto('https://www.district.in/', wait_until='networkidle', timeout=60000)
    time.sleep(12)
    body_text = page.inner_text('body')
    print('body length', len(body_text))
    for token in ['Hyderabad', 'events', 'Hybrid', 'Movies', 'Event']:
        print(token, body_text.count(token))
    snippet = body_text[:2000]
    print('snippet:', snippet)
    browser.close()
