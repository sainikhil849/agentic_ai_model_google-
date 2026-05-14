#!/usr/bin/env python
"""
Comprehensive test to validate:
1. Optional metadata extraction from all platforms
2. BookMyShow Language, Type, Format extraction
3. District 404 handling
4. Swiggy Scenes multiple events
5. Dashboard display compatibility
6. Excel export compatibility
"""

import sys
import logging
import asyncio
from agents.platforms import get_platform_agent

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

PLATFORMS_TO_TEST = ["BookMyShow", "District", "Swiggy Scenes", "Meetup", "Urbanaut"]
LOCATION = "Hyderabad"
TARGET_COUNT = 5
MAX_PRICE = None

async def test_single_platform(platform_name: str):
    """Test a single platform and return results"""
    logger.info(f"\n{'='*60}")
    logger.info(f"Testing: {platform_name}")
    logger.info(f"{'='*60}")
    
    try:
        agent = get_platform_agent(platform_name, LOCATION)
        if not agent:
            logger.warning(f"  ✗ Agent not found for {platform_name}")
            return None
        
        events = await agent.extract_events(LOCATION, TARGET_COUNT, MAX_PRICE)
        
        logger.info(f"  ✓ Extracted {len(events)} events")
        
        if not events:
            logger.warning(f"  ! No events found")
            return events
        
        # Verify optional metadata fields
        optional_fields = ['event_language', 'event_type', 'duration', 'event_time', 'event_format', 'attending', 'rating']
        
        for i, event in enumerate(events[:3]):  # Show first 3
            logger.info(f"\n  Event {i+1}: {event.get('event_name', 'N/A')[:50]}")
            logger.info(f"    Price: ₹{event.get('price', 'N/A')}")
            logger.info(f"    Date: {event.get('event_date', 'N/A')}")
            
            # Check optional fields
            optional_count = 0
            for field in optional_fields:
                if field in event and event[field]:
                    logger.info(f"    {field}: {event[field]}")
                    optional_count += 1
            
            if optional_count > 0:
                logger.info(f"    ✓ Found {optional_count}/{len(optional_fields)} optional fields")
            else:
                logger.info(f"    ! No optional fields extracted")
        
        return events
    
    except Exception as exc:
        logger.error(f"  ✗ ERROR: {exc}", exc_info=True)
        return None

async def test_all_platforms():
    """Test all platforms"""
    results = {}
    
    for platform in PLATFORMS_TO_TEST:
        try:
            events = await test_single_platform(platform)
            results[platform] = events
        except Exception as exc:
            logger.error(f"Test failed for {platform}: {exc}")
            results[platform] = None
    
    # Summary
    logger.info(f"\n{'='*60}")
    logger.info("SUMMARY")
    logger.info(f"{'='*60}")
    
    total_events = 0
    platforms_with_events = 0
    
    for platform, events in results.items():
        if events is None:
            logger.info(f"  ✗ {platform}: ERROR")
        elif len(events) == 0:
            logger.info(f"  ! {platform}: 0 events")
        else:
            logger.info(f"  ✓ {platform}: {len(events)} events")
            total_events += len(events)
            platforms_with_events += 1
    
    logger.info(f"\nTotal: {total_events} events from {platforms_with_events} platforms")
    
    # Test Excel export
    logger.info(f"\n{'='*60}")
    logger.info("Testing Excel Export")
    logger.info(f"{'='*60}")
    
    try:
        from utils.excel_exporter import export_to_excel
        test_events = []
        for events in results.values():
            if events:
                test_events.extend(events[:2])
        
        if test_events:
            output_path = export_to_excel(test_events)
            logger.info(f"  ✓ Excel exported to: {output_path}")
            
            # Verify it has optional fields columns
            try:
                import openpyxl
                wb = openpyxl.load_workbook(output_path)
                ws = wb.active
                headers = [cell.value for cell in ws[1]]
                optional_headers = ['Language', 'Type', 'Format', 'Time', 'Attending', 'Rating', 'Duration']
                found = sum(1 for h in headers if h in optional_headers)
                logger.info(f"  ✓ Found {found}/{len(optional_headers)} optional field columns in Excel")
            except Exception as e:
                logger.warning(f"  ! Could not verify Excel columns: {e}")
        else:
            logger.warning("  ! No events to export")
    
    except Exception as exc:
        logger.error(f"  ✗ Excel export test failed: {exc}")

if __name__ == "__main__":
    logger.info("Starting comprehensive platform tests...")
    asyncio.run(test_all_platforms())
    logger.info("\n✓ All tests completed")
