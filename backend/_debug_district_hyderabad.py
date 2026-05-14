from playwright.sync_api import sync_playwright
import time
with sync_playwright() as p:
    browser = p.chromium.launch(headless=False, args=['--no-sandbox','--disable-dev-shm-usage'])
    context = browser.new_context(viewport={'width':1920,'height':1080}, locale='en-IN', timezone_id='Asia/Kolkata')
    page = context.new_page()
    page.goto('https://www.district.in/events/hyderabad-ticket-booking', wait_until='domcontentloaded', timeout=60000)
    time.sleep(12)
    for i in range(15):
        page.evaluate('window.scrollBy(0, 2500)')
        time.sleep(1)
    content = page.content()
    print('content length', len(content))
    print(content[:1500].replace('\n',' '))
    anchors = page.query_selector_all("a[href*='/events/'], a[href*='/activities/']")
    urls=set()
    for a in anchors:
        href = a.get_attribute('href') or ''
        if href.startswith('/'):
            urls.add('https://www.district.in'+href)
        else:
            urls.add(href)
    print('anchors', len(anchors), 'unique', len(urls))
    print(list(urls)[:100])
    browser.close()
