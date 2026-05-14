"""
Debug District HTML structure to find correct selectors
"""

import sys
import time
from playwright.sync_api import sync_playwright

sys.path.insert(0, r'c:\Users\saini\OneDrive\Desktop\codes\New folder\backend')

def debug_district_structure():
    """Inspect District.in HTML to find correct selectors"""
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context()
        page = context.new_page()
        
        try:
            # Navigate to Mumbai events
            url = "https://www.district.in/events-in-mumbai/"
            print(f"\n📍 Navigating to: {url}")
            page.goto(url, wait_until="networkidle", timeout=45000)
            
            # Scroll to load content
            print("⏳ Scrolling to load content...")
            for i in range(3):
                page.evaluate("window.scrollBy(0, 500)")
                time.sleep(1)
            
            # Try different selectors
            selectors_to_try = [
                "a[href*='/event/']",
                "a[class*='event']",
                "article",
                "[class*='card']",
                "[class*='event-card']",
                "div[class*='event']",
                ".event-link",
                "a.event-card",
                "[data-testid*='event']",
                "h2",
                "h3",
                "a[href*='district.in/event']",
                ".dds-h-full",
                "a:has(h3)",
                "a:has(h2)"
            ]
            
            print("\n" + "="*80)
            print("TESTING SELECTORS")
            print("="*80)
            
            for selector in selectors_to_try:
                try:
                    elements = page.query_selector_all(selector)
                    if elements:
                        print(f"\n✓ Selector found: {selector}")
                        print(f"  Count: {len(elements)}")
                        
                        # Get first element sample
                        if len(elements) > 0:
                            first_elem = elements[0]
                            try:
                                text = first_elem.inner_text()[:100]
                                href = first_elem.get_attribute("href") if "a" in selector.lower() else None
                                print(f"  Sample text: {text}")
                                if href:
                                    print(f"  Sample href: {href}")
                            except:
                                pass
                except Exception as e:
                    pass
            
            # Get page HTML sample
            print("\n" + "="*80)
            print("PAGE HTML SAMPLE (first 2000 chars)")
            print("="*80)
            html = page.content()
            print(html[:2000])
            
            # Save full HTML for inspection
            html_file = r'c:\Users\saini\OneDrive\Desktop\codes\New folder\backend\debug_district_html.html'
            with open(html_file, 'w', encoding='utf-8') as f:
                f.write(html)
            print(f"\n✓ Full HTML saved to: {html_file}")
            
            # Keep browser open for inspection
            print("\n✓ Browser open for inspection. Close it when done.")
            time.sleep(30)  # Keep open for 30 seconds
            
        except Exception as e:
            print(f"❌ Error: {e}")
        finally:
            browser.close()

if __name__ == "__main__":
    debug_district_structure()
