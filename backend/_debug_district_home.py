from playwright.sync_api import sync_playwright
import time

with sync_playwright() as p:
    browser = p.chromium.launch(headless=False, args=['--no-sandbox', '--disable-dev-shm-usage'])
    context = browser.new_context(viewport={'width': 1920, 'height': 1080}, locale='en-IN', timezone_id='Asia/Kolkata')
    page = context.new_page()
    page.goto('https://www.district.in/', wait_until='networkidle', timeout=60000)
    time.sleep(5)
    body = page.content()
    print('body snippet:', body[:1000].replace('\n', ' '))
    next_data = None
    try:
        next_data = page.evaluate('window.__NEXT_DATA__')
    except Exception as exc:
        print('next_data eval error', exc)
    print('next_data type', type(next_data))
    if next_data:
        from json import dumps
        print('next_data keys', list(next_data.keys())[:20])
        print('next_data length', len(str(next_data))[:200])
    print('page title', page.title())
    browser.close()
