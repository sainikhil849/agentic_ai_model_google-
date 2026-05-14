#!/usr/bin/env python3
"""
Inspect District.in page structure directly
"""

from playwright.sync_api import sync_playwright
import json

print("\n" + "="*80)
print("DISTRICT.IN PAGE INSPECTION")
print("="*80)

with sync_playwright() as p:
    browser = p.chromium.launch(headless=False)
    page = browser.new_page()
    
    # Go to Bangalore events page
    print("\n[*] Loading https://www.district.in/events/bengaluru...")
    page.goto("https://www.district.in/events/bengaluru", wait_until="networkidle", timeout=40000)
    page.wait_for_timeout(1500)
    
    # Scroll to load events
    print("[*] Scrolling...")
    for _ in range(3):
        page.evaluate("window.scrollBy(0, 800)")
        page.wait_for_timeout(600)
    
    print("[OK] Page ready")
    
    # Test selectors
    tests = {
        'a[href*="/event/"]': "Event links (direct)",
        'a[href*="/activity/"]': "Activity links",
        '[class*="card"]': "Card elements",
        '[class*="Event"]': "Event class elements",
    }
    
    print("\n[SELECTOR TESTS]")
    print("-" * 80)
    
    for selector, desc in tests.items():
        elems = page.query_selector_all(selector)
        print(f"{desc:40} ({selector:30}): {len(elems):3} found")
        if elems and len(elems) > 0:
            # Show first element
            text = elems[0].inner_text()[:70]
            href = elems[0].get_attribute('href') or "N/A"
            print(f"  First: {text}")
            if href != "N/A":
                print(f"  Href:  {href}")
    
    # Check for Next.js data
    print("\n[NEXT.JS DATA]")
    print("-" * 80)
    try:
        next_data = page.evaluate("window.__NEXT_DATA__")
        if next_data:
            # Find events in the data
            data_str = json.dumps(next_data)
            if "event" in data_str.lower():
                print("✓ Found event data in __NEXT_DATA__")
                if "props" in next_data:
                    print("  Structure: Has props")
                if "pageProps" in next_data.get("props", {}):
                    print("  Structure: Has pageProps")
            else:
                print("✗ No event data in __NEXT_DATA__")
        else:
            print("✗ No __NEXT_DATA__ found")
    except Exception as e:
        print(f"✗ Error checking __NEXT_DATA__: {e}")
    
    # Show actual event links found
    print("\n[EVENT LINKS FOUND]")
    print("-" * 80)
    links = page.query_selector_all('a[href*="/event/"]')
    print(f"Total: {len(links)} event links")
    for i, link in enumerate(links[:5]):
        href = link.get_attribute('href') or ""
        text = link.inner_text()[:60]
        print(f"  {i+1}. {text}")
        print(f"     {href}")
    
    print("\n" + "="*80)
    print("Keep browser open for manual inspection...")
    
    input("Press Enter to continue...")
    browser.close()
