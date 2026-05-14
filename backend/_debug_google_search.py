from playwright.sync_api import sync_playwright
import time

with sync_playwright() as p:
    browser = p.chromium.launch(headless=False, args=['--no-sandbox','--disable-dev-shm-usage'])
    context = browser.new_context(viewport={'width':1920,'height':1080}, locale='en-IN', timezone_id='Asia/Kolkata')
    page = context.new_page()
    q = 'site:swiggy.com scenes Hyderabad events'
    page.goto(f'https://www.google.com/search?q={q}', wait_until='domcontentloaded', timeout=45000)
    time.sleep(8)
    content = page.content()
    print('len', len(content))
    print(content[:4000].replace('\n',' '))
    anchors = page.query_selector_all('a')
    print('anchors count', len(anchors))
    for i, a in enumerate(anchors[:50]):
        try:
            href = a.get_attribute('href') or ''
            txt = a.inner_text().strip()
            print(i, href[:200], txt[:100])
        except Exception as exc:
            print('err', exc)
    browser.close()
