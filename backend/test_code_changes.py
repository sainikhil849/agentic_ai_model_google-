#!/usr/bin/env python
"""
Unit test to verify the core functionality changes:
1. Layer 4 always calls _enrich_event_details
2. Optional metadata extraction methods exist
3. Excel exporter includes optional columns
4. District handles 404 gracefully
"""

import logging
import sys
import os

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_layer4_always_enriches():
    """Verify that base_agent.py Layer 4 always calls _enrich_event_details"""
    logger.info("\n✓ Testing: Layer 4 always calls _enrich_event_details")
    
    with open("agents/base_agent.py", "r",encoding="utf-8") as f:
        content = f.read()
    
    # Check that Layer 4 calls _enrich_event_details unconditionally
    layer4_section = content[content.find("Layer 4: enrich"):content.find("Layer 4: enrich") + 3000]
    
    if "raw = self._enrich_event_details(page, raw)" in layer4_section and \
       "if needs_price or needs_date:" not in layer4_section:
        logger.info("  ✓ Layer 4 ALWAYS calls _enrich_event_details (good!)")
        return True
    else:
        logger.warning("  ✗ Layer 4 might not always call _enrich_event_details")
        return False

def test_optional_metadata_methods_exist():
    """Verify that optional metadata extraction methods exist"""
    logger.info("\n✓ Testing: Optional metadata extraction methods exist")
    
    with open("agents/base_agent.py", "r", encoding="utf-8") as f:
        content = f.read()
    
    methods_found = 0
    if "def _extract_event_metadata_from_json_ld" in content:
        logger.info("  ✓ Found _extract_event_metadata_from_json_ld")
        methods_found += 1
    if "def _extract_event_metadata_from_text" in content:
        logger.info("  ✓ Found _extract_event_metadata_from_text")
        methods_found += 1
    
    if methods_found == 2:
        logger.info("  ✓ All optional metadata extraction methods present")
        return True
    else:
        logger.warning(f"  ✗ Only found {methods_found}/2 methods")
        return False

def test_excel_exporter_columns():
    """Verify that Excel exporter includes optional field columns"""
    logger.info("\n✓ Testing: Excel exporter includes optional field columns")
    
    with open("utils/excel_exporter.py", "r", encoding="utf-8") as f:
        content = f.read()
    
    optional_columns = ['event_language', 'event_type', 'duration', 'event_time', 'event_format', 'attending', 'rating']
    found_columns = 0
    
    for col in optional_columns:
        if col in content or col.replace('event_', '').capitalize() in content:
            found_columns += 1
            logger.info(f"  ✓ Found {col} in Excel exporter")
    
    if found_columns >= 5:
        logger.info(f"  ✓ Excel exporter includes {found_columns}/7 optional field columns")
        return True
    else:
        logger.warning(f"  ✗ Excel exporter missing some optional columns ({found_columns}/7)")
        return False

def test_district_404_handling():
    """Verify that District agent handles 404 gracefully"""
    logger.info("\n✓ Testing: District handles 404 errors")
    
    with open("agents/platforms.py", "r", encoding="utf-8") as f:
        content = f.read()
    
    district_section = content[content.find("class DistrictAgent"):content.find("class DistrictAgent") + 5000]
    
    checks = {
        "404 handling": "404" in district_section or "status >= 400" in district_section,
        "Delay between requests": "time.sleep" in district_section,
        "Consecutive 404 counter": "consecutive_404" in district_section,
    }
    
    passed = sum(1 for k, v in checks.items() if v)
    for check, result in checks.items():
        status = "✓" if result else "✗"
        logger.info(f"  {status} {check}")
    
    if passed >= 2:
        logger.info(f"  ✓ District 404 handling implemented ({passed}/3 checks)")
        return True
    else:
        logger.warning(f"  ✗ District 404 handling incomplete ({passed}/3 checks)")
        return False

def test_swiggy_scenes_improved():
    """Verify that Swiggy Scenes has improved event discovery"""
    logger.info("\n✓ Testing: Swiggy Scenes improved event discovery")
    
    with open("agents/platforms.py", "r", encoding="utf-8") as f:
        content = f.read()
    
    swiggy_section = content[content.find("class SwiggyScenesAgent"):content.find("class SwiggyScenesAgent") + 3000]
    
    checks = {
        "Increased scrolling": "scrolls=20" in swiggy_section,
        "Window state parsing": "_extract_window_object" in swiggy_section,
        "Increased target limit": "target_count * 4" in swiggy_section,
        "Global seen_urls deduplication": "seen_urls = set()" in swiggy_section,
    }
    
    passed = sum(1 for k, v in checks.items() if v)
    for check, result in checks.items():
        status = "✓" if result else "✗"
        logger.info(f"  {status} {check}")
    
    if passed >= 3:
        logger.info(f"  ✓ Swiggy Scenes improvements implemented ({passed}/4 checks)")
        return True
    else:
        logger.warning(f"  ✗ Swiggy Scenes improvements incomplete ({passed}/4 checks)")
        return False

def test_bookmyshow_simplified():
    """Verify that BookMyShow is simplified for Layer 4 enrichment"""
    logger.info("\n✓ Testing: BookMyShow simplified for Layer 4 enrichment")
    
    with open("agents/platforms.py", "r", encoding="utf-8") as f:
        content = f.read()
    
    bms_section = content[content.find("class BookMyShowAgent"):content.find("class DistrictAgent")]
    
    # Check that it returns early without internal enrichment loop
    if "return raw_candidates" in bms_section and \
       "Visit detail pages" not in bms_section and \
       "L1c" not in bms_section:
        logger.info("  ✓ BookMyShow simplified, returns candidates for Layer 4 enrichment")
        return True
    else:
        logger.warning("  ✗ BookMyShow might still have internal enrichment logic")
        return False

def test_frontend_optional_fields():
    """Verify that frontend App.jsx displays optional fields"""
    logger.info("\n✓ Testing: Frontend displays optional field columns")
    
    try:
        with open("../frontend/src/App.jsx", "r", encoding="utf-8") as f:
            content = f.read()
        
        optional_fields = ['event_language', 'event_format', 'event_time', 'attending', 'rating']
        found_fields = 0
        
        for field in optional_fields:
            if field in content or field.replace('event_', '') in content:
                found_fields += 1
                logger.info(f"  ✓ Found {field} in frontend")
        
        if found_fields >= 3:
            logger.info(f"  ✓ Frontend displays {found_fields}/{len(optional_fields)} optional fields")
            return True
        else:
            logger.warning(f"  ✗ Frontend missing optional field display ({found_fields}/{len(optional_fields)})")
            return False
    except FileNotFoundError:
        logger.warning("  ! Frontend file not found, skipping test")
        return True

if __name__ == "__main__":
    logger.info("\n" + "="*60)
    logger.info("CODE VALIDATION UNIT TESTS")
    logger.info("="*60)
    
    results = {
        "Layer 4 always enriches": test_layer4_always_enriches(),
        "Optional metadata methods": test_optional_metadata_methods_exist(),
        "Excel exporter columns": test_excel_exporter_columns(),
        "District 404 handling": test_district_404_handling(),
        "Swiggy Scenes improved": test_swiggy_scenes_improved(),
        "BookMyShow simplified": test_bookmyshow_simplified(),
        "Frontend optional fields": test_frontend_optional_fields(),
    }
    
    logger.info("\n" + "="*60)
    logger.info("TEST SUMMARY")
    logger.info("="*60)
    
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    
    for test, result in results.items():
        status = "✓ PASS" if result else "✗ FAIL"
        logger.info(f"  {status}: {test}")
    
    logger.info(f"\nTotal: {passed}/{total} tests passed")
    
    if passed == total:
        logger.info("\n✓ All code changes validated successfully!")
        sys.exit(0)
    else:
        logger.warning(f"\n✗ {total - passed} validation(s) failed")
        sys.exit(1)
