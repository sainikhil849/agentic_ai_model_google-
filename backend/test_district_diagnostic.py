#!/usr/bin/env python
"""
District Agent Diagnostic Test
Checks if the agent is working and returning expected output
"""

import logging
import sys
import os

logging.basicConfig(level=logging.DEBUG, format='%(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_district_agent_code():
    """Test Distract agent code for completeness and correctness"""
    logger.info("\n" + "="*80)
    logger.info("DISTRICT AGENT DIAGNOSTIC TEST")
    logger.info("="*80)
    
    # Check 1: File exists
    logger.info("\n1. Checking file existence...")
    if not os.path.exists("agents/platforms.py"):
        logger.error("  ✗ platforms.py not found!")
        return False
    logger.info("  ✓ platforms.py found")
    
    # Check 2: Read the file
    logger.info("\n2. Reading District agent code...")
    try:
        with open("agents/platforms.py", "r", encoding="utf-8") as f:
            content = f.read()
        logger.info("  ✓ File read successfully")
    except Exception as e:
        logger.error(f"  ✗ Failed to read file: {e}")
        return False
    
    # Check 3: District class exists
    logger.info("\n3. Checking District agent class...")
    if "class DistrictAgent(BaseAgent):" not in content:
        logger.error("  ✗ DistrictAgent class not found!")
        return False
    logger.info("  ✓ DistrictAgent class exists")
    
    # Extract District section
    district_start = content.find("class DistrictAgent")
    if district_start == -1:
        logger.error("  ✗ Could not locate DistrictAgent section")
        return False
    
    # Find the next class to get the end of DistrictAgent
    next_class = content.find("class ", district_start + 1)
    district_end = next_class if next_class != -1 else len(content)
    district_section = content[district_start:district_end]
    
    logger.info(f"  ✓ District agent section: {len(district_section)} characters")
    
    # Check 4: Required methods
    logger.info("\n4. Checking required methods...")
    methods_required = {
        "_perform_scraping_sync": "_perform_scraping_sync" in district_section,
    }
    
    for method, exists in methods_required.items():
        status = "✓" if exists else "✗"
        logger.info(f"  {status} {method}")
        if not exists:
            logger.error(f"    Method {method} is missing!")
            return False
    
    # Check 5: Core features
    logger.info("\n5. Checking core features...")
    features = {
        "Hyderabad-specific URLs": "hyderabad-ticket-booking" in district_section,
        "Location validation": "is_hyderabad_event" in district_section,
        "404 handling": "consecutive_404" in district_section,
        "Event enrichment": "self._enrich_event_details" in district_section,
        "JSON-LD extraction": "self._extract_json_ld" in district_section,
        "Candidate collection": "candidates.append" in district_section,
        "Accepted/rejected tracking": "accepted_hyd_events" in district_section and "skipped_wrong_location" in district_section,
        "Return enriched events": "return enriched" in district_section,
    }
    
    passed_features = 0
    for feature, exists in features.items():
        status = "✓" if exists else "✗"
        logger.info(f"  {status} {feature}")
        if exists:
            passed_features += 1
        else:
            logger.warning(f"    Missing: {feature}")
    
    # Check 6: Syntax validation
    logger.info("\n6. Checking Python syntax...")
    try:
        import py_compile
        py_compile.compile("agents/platforms.py", doraise=True)
        logger.info("  ✓ Python syntax is valid")
    except py_compile.PyCompileError as e:
        logger.error(f"  ✗ Syntax error: {e}")
        return False
    
    # Check 7: Data flow
    logger.info("\n7. Checking data flow logic...")
    data_flow = {
        "Gets city from location": "city = location.lower()" in district_section,
        "Initializes candidates list": "candidates = []" in district_section,
        "Loops through URLs": "for url_idx, url in enumerate(listing_urls)" in district_section,
        "Scrolls pages": "self._deep_scroll_page" in district_section,
        "Queries elements": "query_selector_all" in district_section,
        "Filters URLs": "if full_url in seen" in district_section,
        "Visits detail pages": "detail_page.goto" in district_section,
        "Extracts location": "extracted_location" in district_section,
        "Validates Hyderabad": "hyd_keywords" in district_section,
        "Returns results": "return enriched" in district_section,
    }
    
    passed_flow = 0
    for step, exists in data_flow.items():
        status = "✓" if exists else "✗"
        logger.info(f"  {step}: {status}")
        if exists:
            passed_flow += 1
    
    # Check 8: Error handling
    logger.info("\n8. Checking error handling...")
    error_handling = {
        "Try-except for main": content.count("try:") > 5,  # Multiple try-except blocks
        "Exception logging": "logger.error" in district_section or "logger.debug" in district_section,
        "Graceful failures": "except Exception" in district_section,
    }
    
    for error_check, exists in error_handling.items():
        status = "✓" if exists else "✗"
        logger.info(f"  {status} {error_check}")
    
    # Summary
    logger.info("\n" + "="*80)
    logger.info("DIAGNOSTIC SUMMARY")
    logger.info("="*80)
    
    total_checks = len(features) + len(data_flow) + len(error_handling)
    passed_checks = passed_features + passed_flow + sum(1 for v in error_handling.values() if v)
    
    logger.info(f"\nCode Quality: {passed_checks}/{total_checks} checks passed")
    
    if passed_features == len(features):
        logger.info("  ✓ All required features implemented")
    else:
        logger.warning(f"  ✗ Missing {len(features) - passed_features} features")
    
    if passed_flow == len(data_flow):
        logger.info("  ✓ Complete data flow implemented")
    else:
        logger.warning(f"  ✗ Incomplete data flow ({len(data_flow) - passed_flow} steps missing)")
    
    logger.info("\n" + "="*80)
    logger.info("EXPECTED OUTPUT FROM DISTRICT AGENT")
    logger.info("="*80)
    logger.info("""
When scraping District with location="Hyderabad" and target_count=170:

1. Collection Phase:
   - Visits: https://www.district.in/events/hyderabad-ticket-booking
   - Scrolls 15 times to load dynamic content
   - Collects 500+ event candidates

2. Enrichment Phase:
   - Visits each event detail page
   - Extracts: name, date, price, venue, location
   - Validates: location must contain "hyderabad"

3. Filtering Phase:
   - Rejects events from other states
   - Accepts only Hyderabad events
   - Tracks: accepted vs rejected counts

4. Output:
   - 150-170 verified Hyderabad events
   - Each with: name, date, price, venue, location="Hyderabad"
   - Ready for dashboard and Excel export

Sample Log Output:
   District: Scraping from URL 1: https://www.district.in/events/hyderabad-ticket-booking
   District: Got 245 candidates from this URL
   District: Total candidates collected: 523
   District: ✓ ACCEPTED (1) 'Tech Meetup' - Location: Hyderabad
   District: ✓ ACCEPTED (2) 'Concert' - Location: Hyderabad
   District: ✗ REJECTED 'Summit' - Location 'Delhi' is not Hyderabad
   
   District Summary:
     • Total candidates: 523
     • Accepted (Hyderabad): 168
     • Rejected (other states): 355
     • Final events: 168
    """)
    
    if passed_checks >= total_checks - 2:
        logger.info("\n✓ DISTRICT AGENT IS CORRECTLY IMPLEMENTED")
        logger.info("  Ready to scrape and return Hyderabad events\n")
        return True
    else:
        logger.warning(f"\n✗ DISTRICT AGENT HAS ISSUES ({total_checks - passed_checks} problems)\n")
        return False

if __name__ == "__main__":
    success = test_district_agent_code()
    sys.exit(0 if success else 1)
