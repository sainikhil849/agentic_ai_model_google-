from playwright.sync_api import sync_playwright
import time

with sync_playwright() as p:
    browser=p.chromium.launch(headless=True)
    context=browser.new_context(viewport={'width':1920,'height':1080}, locale='en-IN', timezone_id='Asia/Kolkata')
    page=context.new_page()
    def log_response(response):
        url=response.url
        if 'district.in' in url and ('json' in url or '/api/' in url or 'search' in url or 'event' in url.lower()):
            print('RESP', response.status, url)
            try:
                text=response.text()
                print('  body len', len(text))
                print('  snippet', text[:400].replace('\n',' '))
            except Exception as e:
                print('  text err', e)

    page.on('response', log_response)
    page.goto('https://www.district.in/events/', wait_until='domcontentloaded', timeout=60000)
    time.sleep(10)
    browser.close()
