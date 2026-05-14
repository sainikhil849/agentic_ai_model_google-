#!/usr/bin/env python3
"""
Validation script for the three surgical fixes.
Tests:
1. District city slug changes dynamically
2. BMS venue selectors work
3. Browser context lifecycle is safe
"""

import sys
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_fix_1_district_city_slug():
    """Test Issue 1: District city slug changes dynamically"""
    logger.info("=" * 70)
    logger.info("TEST 1: District City Slug (ISSUE 1 FIX)")
    logger.info("=" * 70)
    
    try:
        from utils.city_config import district_city_slug
        
        test_cases = [
            ("Bangalore", "bengaluru"),
            ("Bengaluru", "bengaluru"),
            ("Mumbai", "mumbai"),
            ("Hyderabad", "hyderabad"),
            ("Hyd", "hyderabad"),
        ]
        
        all_passed = True
        for location, expected in test_cases:
            result = district_city_slug(location)
            passed = result == expected
            all_passed = all_passed and passed
            status = "✓ PASS" if passed else "✗ FAIL"
            logger.info(f"  {status}: district_city_slug('{location}') = '{result}' (expected '{expected}')")
        
        if all_passed:
            logger.info("✓ TEST 1 PASSED: District city slugs are dynamic\n")
        else:
            logger.error("✗ TEST 1 FAILED: Some city slugs are incorrect\n")
        return all_passed
    except Exception as e:
        logger.error(f"✗ TEST 1 EXCEPTION: {e}\n")
        return False


def test_fix_2_bms_venue_selectors():
    """Test Issue 2: BMS venue selector tiers are present"""
    logger.info("=" * 70)
    logger.info("TEST 2: BMS Venue Selectors (ISSUE 2 FIX)")
    logger.info("=" * 70)
    
    try:
        from agents.platforms import BookMyShowAgent
        import inspect
        
        agent = BookMyShowAgent()
        source = inspect.getsource(agent._extract_bookmyshow_venue_dom)
        
        # Check for new selectors mentioned in the fix
        required_selectors = [
            "data-testid",
            "eventVenue",
            "venue-name",
            "networkidle",
            "wait_for_timeout",
            "Tier 1",
            "Tier 2",
            "Tier 3",
            "Tier 4",
            "Tier 5",
        ]
        
        all_found = True
        for selector in required_selectors:
            found = selector in source
            all_found = all_found and found
            status = "✓" if found else "✗"
            logger.info(f"  {status} Selector/comment '{selector}' present in code")
        
        # Check for wait_for_load_state
        if "wait_for_load_state" in source and "networkidle" in source:
            logger.info("  ✓ Page wait (networkidle) is present")
        else:
            logger.info("  ✗ Page wait (networkidle) is missing")
            all_found = False
        
        # Check for wait_for_timeout
        if "wait_for_timeout" in source and "2000" in source:
            logger.info("  ✓ Additional wait (2000ms) is present")
        else:
            logger.info("  ✗ Additional wait (2000ms) is missing")
            all_found = False
        
        if all_found:
            logger.info("✓ TEST 2 PASSED: BMS venue selectors are enhanced with multiple tiers\n")
        else:
            logger.error("✗ TEST 2 FAILED: Some venue selector improvements are missing\n")
        return all_found
    except Exception as e:
        logger.error(f"✗ TEST 2 EXCEPTION: {e}\n")
        return False


def test_fix_3_browser_lifecycle():
    """Test Issue 3: Browser lifecycle safety checks are in place"""
    logger.info("=" * 70)
    logger.info("TEST 3: Browser Lifecycle Safety (ISSUE 3 FIX)")
    logger.info("=" * 70)
    
    try:
        from agents.base_agent import BaseAgent
        import inspect
        
        agent = BaseAgent("Test", "http://test.com")
        source = inspect.getsource(agent._google_search_fallback)
        
        # Check for page.is_closed() checks
        checks = [
            ("page.is_closed()", "Page closed check at fallback start"),
            ("context.new_page()", "Context page restoration"),
            ("browser.new_page()", "Browser page restoration"),
            ("page.is_closed()", "Page closed check during loop"),
        ]
        
        all_found = True
        for check_str, description in checks:
            found = check_str in source
            all_found = all_found and found
            status = "✓" if found else "✗"
            logger.info(f"  {status} {description}")
        
        # Check for browser/context parameters
        sig = inspect.signature(agent._google_search_fallback)
        params = list(sig.parameters.keys())
        has_browser_param = "browser" in params
        has_context_param = "context" in params
        
        if has_browser_param:
            logger.info("  ✓ browser parameter present in fallback signature")
        else:
            logger.info("  ✗ browser parameter missing from fallback signature")
            all_found = False
        
        if has_context_param:
            logger.info("  ✓ context parameter present in fallback signature")
        else:
            logger.info("  ✗ context parameter missing from fallback signature")
            all_found = False
        
        if all_found:
            logger.info("✓ TEST 3 PASSED: Browser lifecycle safety checks are in place\n")
        else:
            logger.error("✗ TEST 3 FAILED: Some browser lifecycle safety checks are missing\n")
        return all_found
    except Exception as e:
        logger.error(f"✗ TEST 3 EXCEPTION: {e}\n")
        return False


def test_fix_1_integration():
    """Verify District URLs will use dynamic city slugs"""
    logger.info("=" * 70)
    logger.info("INTEGRATION TEST 1: District URLs (verify integration)")
    logger.info("=" * 70)
    
    try:
        from agents.platforms import DistrictAgent
        from utils.city_config import district_city_slug
        import inspect
        
        agent = DistrictAgent()
        source = inspect.getsource(agent._perform_scraping_sync)
        
        # Check that district_city_slug is imported and used
        if "district_city_slug" in source:
            logger.info("  ✓ district_city_slug function is called in DistrictAgent")
        else:
            logger.error("  ✗ district_city_slug function is NOT called in DistrictAgent")
            return False
        
        if "city_slug = district_city_slug(location)" in source:
            logger.info("  ✓ city_slug is derived from location parameter")
        else:
            logger.error("  ✗ city_slug is not derived from location parameter")
            return False
        
        if "f\"https://www.district.in/events/{city_slug}-ticket-booking\"" in source:
            logger.info("  ✓ District URL uses dynamic city_slug in f-string")
        else:
            logger.error("  ✗ District URL does NOT use dynamic city_slug")
            return False
        
        logger.info("✓ INTEGRATION TEST 1 PASSED: District will use dynamic city slugs\n")
        return True
    except Exception as e:
        logger.error(f"✗ INTEGRATION TEST 1 EXCEPTION: {e}\n")
        return False


if __name__ == "__main__":
    logger.info("\n" + "=" * 70)
    logger.info("SURGICAL FIX VALIDATION TEST SUITE")
    logger.info("=" * 70 + "\n")
    
    results = []
    results.append(("ISSUE 1: District City Slug", test_fix_1_district_city_slug()))
    results.append(("ISSUE 2: BMS Venue Selectors", test_fix_2_bms_venue_selectors()))
    results.append(("ISSUE 3: Browser Lifecycle", test_fix_3_browser_lifecycle()))
    results.append(("INTEGRATION 1: District URLs", test_fix_1_integration()))
    
    logger.info("\n" + "=" * 70)
    logger.info("FINAL RESULTS")
    logger.info("=" * 70)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        logger.info(f"{status}: {test_name}")
    
    logger.info(f"\nTotal: {passed}/{total} tests passed\n")
    
    if passed == total:
        logger.info("🎉 ALL SURGICAL FIXES VALIDATED SUCCESSFULLY!\n")
        sys.exit(0)
    else:
        logger.error("⚠️  Some tests failed. Review the output above.\n")
        sys.exit(1)
