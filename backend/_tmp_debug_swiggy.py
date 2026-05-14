from playwright.sync_api import sync_playwright
import time
with sync_playwright() as p:
    browser=p.chromium.launch(headless=False)
    context=browser.new_context(viewport={'width':1920,'height':1080}, locale='en-IN', timezone_id='Asia/Kolkata')
    page=context.new_page()
    try:
        url='https://www.swiggy.com/scenes?city=hyderabad'
        resp=page.goto(url, wait_until='domcontentloaded', timeout=60000)
        print('status', resp.status if resp else None)
        time.sleep(5)
        body = page.content()[:1000]
        print(body)
        cards = page.query_selector_all("a[href*='/scenes/'], a[href*='/city/hyderabad']")
        print('cards', len(cards))
        for c in cards[:20]:
            print(c.get_attribute('href'))
    except Exception as e:
        print('err', e)
    finally:
        browser.close()
