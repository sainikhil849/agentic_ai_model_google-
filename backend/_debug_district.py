from playwright.sync_api import sync_playwright
import time

with sync_playwright() as p:
    browser = p.chromium.launch(headless=False, args=['--no-sandbox', '--disable-dev-shm-usage'])
    context = browser.new_context(viewport={'width': 1920, 'height': 1080}, locale='en-IN', timezone_id='Asia/Kolkata')
    page = context.new_page()
    resp = page.goto('https://www.district.in/events-in-hyderabad/', wait_until='networkidle', timeout=60000)
    print('loaded', page.url)
    print('status', resp.status if resp else 'no response')
    print('content len', len(page.content()))
    print('content snippet', page.content()[:800].replace('\n', ' '))
    for i in range(15):
        page.evaluate('window.scrollBy(0, 2500)')
        time.sleep(1)
    print('scroll done')
    anchors = page.query_selector_all("a[href*='/events/'], a[href*='/activities/']")
    print('anchors count', len(anchors))
    urls = set()
    for a in anchors:
        href = a.get_attribute('href') or ''
        if '/events/' in href or '/activities/' in href:
            urls.add(href if href.startswith('http') else 'https://www.district.in' + href)
    print('distinct urls', len(urls))
    print(list(urls)[:50])
    next_data = page.evaluate('window.__NEXT_DATA__')

    def walk(o):
        if isinstance(o, dict):
            if 'slug' in o and 'name' in o and ('/events/' in str(o['slug']) or '/activities/' in str(o['slug'])):
                yield o
            for v in o.values():
                yield from walk(v)
        elif isinstance(o, list):
            for i in o:
                yield from walk(i)

    slugs = list(walk(next_data))
    print('next_data events', len(slugs))
    browser.close()
