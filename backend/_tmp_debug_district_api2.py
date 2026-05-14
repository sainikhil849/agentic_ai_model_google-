from playwright.sync_api import sync_playwright
import time

with sync_playwright() as p:
    browser=p.chromium.launch(headless=True)
    context=browser.new_context(viewport={'width':1920,'height':1080}, locale='en-IN', timezone_id='Asia/Kolkata')
    page=context.new_page()
    def log_response(response):
        url=response.url
        ct=response.headers.get('content-type','')
        if 'json' in ct.lower() or 'api' in url.lower() or 'graphql' in url.lower() or 'search' in url.lower() or 'district.in' in url.lower():
            print('RESP', response.status, url, ct)
    page.on('response', log_response)
    page.goto('https://www.district.in/events/', wait_until='networkidle', timeout=60000)
    time.sleep(10)
    browser.close()
