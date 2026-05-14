from playwright.sync_api import sync_playwright
import time
paths=['https://www.district.in/events/','https://www.district.in/activities/']
with sync_playwright() as p:
    browser=p.chromium.launch(headless=True)
    context=browser.new_context(viewport={'width':1920,'height':1080}, locale='en-IN', timezone_id='Asia/Kolkata')
    page=context.new_page()
    for path in paths:
        page.goto(path, wait_until='networkidle', timeout=60000)
        time.sleep(1)
        for i in range(10):
            page.evaluate('window.scrollBy(0,2500)')
            time.sleep(0.8)
        anchors=page.query_selector_all("a[href*='/events/'], a[href*='/activities/']")
        urls=set()
        for a in anchors:
            href=a.get_attribute('href') or ''
            if href.startswith('/'):
                urls.add('https://www.district.in'+href)
            else:
                urls.add(href)
        print(path, 'anchors', len(anchors), 'unique', len(urls))
        print(list(urls)[:20])
    browser.close()
