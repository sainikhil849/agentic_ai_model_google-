
import asyncio
import logging
import json
from agents.platforms import BookMyShowAgent
from playwright.sync_api import sync_playwright

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_bms_enrichment_multiple():
    agent = BookMyShowAgent()
    urls = [
        "https://in.bookmyshow.com/events/tempo-tantrums-kenny-sebastian/ET00480918",
        "https://in.bookmyshow.com/events/the-great-indian-science-festival/ET00358282"
    ]
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False, args=[
            "--disable-blink-features=AutomationControlled",
            "--no-sandbox",
        ])
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
            viewport={"width": 1920, "height": 1080},
        )
        page = context.new_page()
        
        try:
            for url in urls:
                logger.info(f"\n{'='*50}\nTESTING URL: {url}\n{'='*50}")
                raw_event = {"url": url, "location": "Hyderabad"}
                
                page.goto(url, wait_until="domcontentloaded", timeout=30000)
                page.wait_for_timeout(2000)
                
                enriched = agent._enrich_event_details(page, raw_event)
                print(json.dumps(enriched, indent=2))
            
        except Exception as e:
            logger.error(f"Enrichment test failed: {e}")
        finally:
            browser.close()

if __name__ == "__main__":
    test_bms_enrichment_multiple()
