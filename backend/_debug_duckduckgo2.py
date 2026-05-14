from playwright.sync_api import sync_playwright
import time
with sync_playwright() as p:
    browser = p.chromium.launch(headless=False, args=['--no-sandbox','--disable-dev-shm-usage'])
    context = browser.new_context(viewport={'width':1920,'height':1080}, locale='en-IN', timezone_id='Asia/Kolkata')
    page = context.new_page()
    q='site:swiggy.com scenes Hyderabad events'
    page.goto(f'https://duckduckgo.com/?q={q}', wait_until='domcontentloaded', timeout=45000)
    time.sleep(8)
    print(page.content()[:5000].replace('\n',' '))
    browser.close()
