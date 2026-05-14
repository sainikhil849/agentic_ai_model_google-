from playwright.sync_api import sync_playwright
import time

queries = [
    'site:district.in Hyderabad District events tickets',
    'site:district.in Hyderabad District upcoming events',
    'site:district.in Hyderabad events',
    'site:district.in Hyderabad things to do',
]

with sync_playwright() as p:
    browser = p.chromium.launch(headless=False, args=['--no-sandbox', '--disable-dev-shm-usage'])
    context = browser.new_context(viewport={'width': 1920, 'height': 1080}, locale='en-IN', timezone_id='Asia/Kolkata')
    page = context.new_page()
    for q in queries:
        print('QUERY:', q)
        page.goto(f'https://www.google.com/search?q={q}', wait_until='domcontentloaded', timeout=45000)
        time.sleep(3)
        results = []
        for h3 in page.query_selector_all('h3'):
            try:
                anchor = h3.evaluate_handle('n => n.closest("a")').as_element()
                if anchor:
                    href = anchor.get_attribute('href') or ''
                    text = h3.inner_text().strip()
                    if href:
                        results.append((href, text))
            except Exception:
                continue
        print('Found', len(results), 'titles')
        for href, text in results[:20]:
            print(href, '|', text)
        print('----')
    browser.close()
