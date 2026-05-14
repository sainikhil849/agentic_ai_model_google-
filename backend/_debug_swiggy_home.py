from playwright.sync_api import sync_playwright
import time
with sync_playwright() as p:
    browser=p.chromium.launch(headless=False,args=['--no-sandbox','--disable-dev-shm-usage'])
    context=browser.new_context(viewport={'width':1920,'height':1080}, locale='en-IN', timezone_id='Asia/Kolkata')
    page=context.new_page()
    page.goto('https://www.swiggy.com/', wait_until='networkidle', timeout=60000)
    time.sleep(12)
    print('title', page.title())
    body = page.inner_text('body')
    print('scenes count', body.lower().count('scenes'))
    print('swiggy count', body.lower().count('swiggy'))
    print('body snippet', body[:1200])
    browser.close()
