from playwright.sync_api import sync_playwright
import time

with sync_playwright() as p:
    browser = p.chromium.launch(headless=False, args=['--no-sandbox', '--disable-dev-shm-usage'])
    context = browser.new_context(viewport={'width': 1920, 'height': 1080}, locale='en-IN', timezone_id='Asia/Kolkata')
    page = context.new_page()

    def log_response(response):
        url = response.url
        status = response.status
        ct = response.headers.get('content-type', '')
        if any(x in url.lower() for x in ['api', 'search', 'event', 'browse', 'hyderabad', 'activities', 'promotions']):
            print('RESP', status, ct, url)
        if 'application/json' in ct and 'district.in' in url:
            try:
                body = response.json()
                print('JSON keys', list(body.keys()) if isinstance(body, dict) else type(body), 'len', len(str(body)) if body else 0)
            except Exception as exc:
                print('JSON parse fail', exc, url)

    page.on('response', log_response)
    page.goto('https://www.district.in/', wait_until='networkidle', timeout=60000)
    time.sleep(10)
    for i in range(8):
        page.evaluate('window.scrollBy(0, 2500)')
        time.sleep(1)
    time.sleep(10)
    browser.close()
