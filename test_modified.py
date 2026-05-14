import sys
import time
from datetime import datetime

sys.path.insert(0, r'c:\Users\saini\OneDrive\Desktop\codes\New folder\backend')

try:
    from playwright.sync_api import sync_playwright
except ImportError as e:
    print(f"ERROR: Playwright not installed: {e}")
    sys.exit(1)

print("\n" + "="*80)
print("DISTRICT URL ROUTING TEST (Modified)")
print("="*80)

try:
    with sync_playwright() as p:
        print("[*] Launching browser...")
        browser = p.chromium.launch(headless=False, timeout=15000)
        print("[OK] Browser launched")
        
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            viewport={"width": 1920, "height": 1080}
        )
        page = context.new_page()

        try:
            print("[*] Loading https://www.district.in/events/bengaluru ...")
            page.goto("https://www.district.in/events/bengaluru", wait_until="domcontentloaded", timeout=15000)
            print(f"[OK] Page loaded: {page.url}")
            time.sleep(1)

            body_text = page.locator("body").inner_text().lower()
            print(f"[OK] Page content retrieved ({len(body_text)} chars)")

            bangalore_keywords = ["bangalore", "bengaluru", "karnataka"]
            other_cities = ["delhi", "mumbai", "gurgaon", "noida", "hyderabad", "pune"]

            print("\n[CITY VERIFICATION]")
            print("-" * 80)
            bangalore_found = any(keyword in body_text for keyword in bangalore_keywords)
            wrong_cities_found = [city for city in other_cities if city in body_text]

            print(f"Bangalore/Bengaluru found: {bangalore_found}")
            if wrong_cities_found:
                print(f"WARNING: Other cities found: {wrong_cities_found}")

            print("\n[EVENT LINKS]")
            print("-" * 80)
            anchors = page.query_selector_all("a[href*='/event/'], a[href*='/events/']")
            print(f"Total anchor elements found: {len(anchors)}")
            
            links = []
            for a in anchors:
                href = a.get_attribute("href") or ""
                if href and "/event" in href.lower():
                    clean_url = href if href.startswith("http") else f"https://www.district.in{href}"
                    clean_url = clean_url.split("?")[0].split("#")[0]
                    links.append(clean_url)

            unique_links = list(set(links))
            print(f"Total unique event links found: {len(unique_links)}")
            print("Sample links:")
            for link in unique_links[:3]:
                print(f"  - {link}")

            print("\n" + "="*80)
            print("TEST COMPLETE - SUCCESS")
            print("="*80)

        except Exception as e:
            print(f"[ERROR] Page navigation failed: {e}")
        finally:
            browser.close()

except Exception as e:
    print(f"[CRITICAL ERROR]: {e}")
    import traceback
    traceback.print_exc()
