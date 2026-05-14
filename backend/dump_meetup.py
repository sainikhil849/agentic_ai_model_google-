from playwright.sync_api import sync_playwright
import sys

def dump():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        try:
            page.goto('https://www.meetup.com/find/?location=in--bangalore&source=EVENTS', timeout=60000)
            content = page.content()
            with open('meetup_dom.html', 'w', encoding='utf-8') as f:
                f.write(content)
        except Exception as e:
            print(f"Error: {e}", file=sys.stderr)
        finally:
            browser.close()

if __name__ == "__main__":
    dump()
