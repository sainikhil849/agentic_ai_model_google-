#!/usr/bin/env python3
"""
DISTRICT URL ROUTING TEST
Verify that https://www.district.in/events/bengaluru loads Bangalore events only
"""

import sys
import time
from datetime import datetime

sys.path.insert(0, r'c:\Users\saini\OneDrive\Desktop\codes\New folder\backend')

from playwright.sync_api import sync_playwright
import logging

logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)

def test_url_routing():
    print("\n" + "="*80)
    print("DISTRICT URL ROUTING TEST")
    print("="*80)
    print(f"Testing: https://www.district.in/events/bengaluru")
    print("Expected: Only Bangalore/Bengaluru events")
    print("="*80 + "\n")
    
    with sync_playwright() as p:
        # Use headless=False to avoid anti-bot detection
        browser = p.chromium.launch(
            headless=False,
            args=[
                "--disable-blink-features=AutomationControlled",
                "--no-sandbox",
                "--disable-dev-shm-usage",
            ]
        )
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
            viewport={"width": 1920, "height": 1080}
        )
        page = context.new_page()
        
        # Remove webdriver flag
        page.add_init_script("Object.defineProperty(navigator,'webdriver',{get:()=>undefined})")
        
        try:
            # Navigate directly to Bangalore events
            print("[*] Loading https://www.district.in/events/bengaluru ...")
            page.goto("https://www.district.in/events/bengaluru", wait_until="domcontentloaded", timeout=30000)
            print("[*] Waiting for content to render...")
            time.sleep(3)
            
            # Check URL first
            current_url = page.url
            print(f"[OK] Page loaded: {current_url}")
            
            # Scroll to load dynamic content
            print("[*] Scrolling to load events...")
            try:
                for scroll_iter in range(3):
                    print(f"  Scroll {scroll_iter + 1}/3...")
                    page.evaluate("window.scrollBy(0, 2000)")
                    time.sleep(1.5)
            except Exception as scroll_err:
                print(f"[!] Scroll error (continuing): {scroll_err}")
            
            # Get body text with error handling
            try:
                body_text = page.locator("body").inner_text().lower()
                body_len = len(body_text)
                print(f"[OK] Page content length: {body_len} characters")
                
                if body_len < 500:
                    print("[!] WARNING: Page content seems minimal")
            except Exception as text_err:
                print(f"[!] Could not read page text: {text_err}")
                body_text = ""
                body_len = 0
            
            # Look for city indicators
            bangalore_keywords = ["bangalore", "bengaluru", "karnataka"]
            other_cities = ["delhi", "mumbai", "gurgaon", "noida", "hyderabad", "pune"]
            
            print("\n[CITY VERIFICATION]")
            print("-" * 80)
            
            if body_len > 0:
                bangalore_found = any(keyword in body_text for keyword in bangalore_keywords)
                wrong_cities_found = [city for city in other_cities if city in body_text]
                
                print(f"Bangalore/Bengaluru found in page: {bangalore_found}")
                if wrong_cities_found:
                    print(f"WARNING: Other cities found: {wrong_cities_found}")
                else:
                    print("GOOD: No other cities detected")
            else:
                print("[!] No content to analyze")
            
            # Extract event links
            print("\n[EVENT LINKS]")
            print("-" * 80)
            try:
                anchors = page.query_selector_all("a[href*='/event/'], a[href*='/events/']")
                links = []
                for a in anchors:
                    href = a.get_attribute("href") or ""
                    if href and "/event" in href.lower():
                        clean_url = href if href.startswith("http") else f"https://www.district.in{href}"
                        clean_url = clean_url.split("?")[0].split("#")[0]
                        links.append(clean_url)
                
                unique_links = list(set(links))
                print(f"Total unique event links found: {len(unique_links)}")
                if unique_links:
                    print("Sample links:")
                    for link in unique_links[:3]:
                        print(f"  - {link}")
                else:
                    print("[!] No event links found - content may not have loaded")
            except Exception as link_err:
                print(f"[!] Error extracting links: {link_err}")
            
            print("\n" + "="*80)
            print("URL ROUTING TEST COMPLETE")
            print("="*80)
            
            time.sleep(2)  # Keep browser open to see results
            
        except Exception as e:
            print(f"\n[ERROR] Test failed: {e}")
            import traceback
            traceback.print_exc()
        finally:
            try:
                browser.close()
            except:
                pass

if __name__ == "__main__":
    test_url_routing()
