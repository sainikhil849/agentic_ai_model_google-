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
        if 'district.in' in url and ('json' in ct or '/api/' in url or '/_next/' in url or 'events' in url):
            print('RESP', status, ct, url)

    page.on('response', log_response)
    page.goto('https://www.district.in/events-in-hyderabad/', wait_until='networkidle', timeout=60000)
    print('loaded', page.url)
    time.sleep(5)
    for i in range(12):
        page.evaluate('window.scrollBy(0, 2500)')
        time.sleep(1)
    print('after scroll', page.url)
    time.sleep(5)
    browser.close()
