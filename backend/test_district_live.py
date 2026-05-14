#!/usr/bin/env python
"""
District Agent Live Test
Actually runs the agent to see if it works
"""

import asyncio
import logging
import sys
import os
from pathlib import Path

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def test_district_agent_live():
    """Test District agent with actual scraping"""
    logger.info("=" * 80)
    logger.info("DISTRICT AGENT LIVE TEST")
    logger.info("=" * 80)
    
    try:
        # Import the agent
        logger.info("\n1. Importing District Agent...")
        from agents.platforms import DistrictAgent
        logger.info("   ✓ Import successful")
        
        # Create agent instance
        logger.info("\n2. Creating agent instance...")
        agent = DistrictAgent()
        logger.info("   ✓ Agent created")
        
        # Test with small target_count for quick feedback
        logger.info("\n3. Running agent with target_count=10 (quick test)...")
        logger.info("   Location: Hyderabad")
        logger.info("   This will scrape District.in and return Hyderabad events only")
        
        try:
            events = await agent.extract_events(
                location="Hyderabad",
                target_count=10  # Small test count
            )
            
            logger.info(f"\n   ✓ Scraping completed!")
            logger.info(f"   ✓ Total events returned: {len(events)}")
            
            if events:
                logger.info("\n4. Sample of returned events:")
                for i, event in enumerate(events[:3], 1):
                    logger.info(f"\n   Event {i}:")
                    logger.info(f"     - Name: {event.get('event_name', 'N/A')}")
                    logger.info(f"     - Date: {event.get('event_date', 'N/A')}")
                    logger.info(f"     - Price: {event.get('price', 'N/A')}")
                    logger.info(f"     - Venue: {event.get('venue', 'N/A')}")
                    logger.info(f"     - Location: {event.get('location', 'N/A')}")
                    logger.info(f"     - Link: {event.get('event_link', 'N/A')}")
            else:
                logger.warning("\n   ✗ NO EVENTS RETURNED!")
                logger.warning("   Check the logs above for errors")
                return False
            
            logger.info("\n" + "=" * 80)
            logger.info("TEST RESULTS")
            logger.info("=" * 80)
            
            # Validate data quality
            logger.info("\n5. Validating data quality...")
            
            hyderabad_count = 0
            non_hyderabad_count = 0
            
            for event in events:
                location = event.get('location', '').lower()
                if 'hyderabad' in location or 'hyd' in location:
                    hyderabad_count += 1
                else:
                    non_hyderabad_count += 1
                    logger.warning(f"   ⚠ Non-Hyderabad event found: '{event.get('event_name')}' in {event.get('location')}")
            
            logger.info(f"\n   • Total events: {len(events)}")
            logger.info(f"   • Hyderabad events: {hyderabad_count} ({100*hyderabad_count//len(events) if events else 0}%)")
            logger.info(f"   • Non-Hyderabad events: {non_hyderabad_count}")
            
            if non_hyderabad_count == 0 and len(events) > 0:
                logger.info("\n   ✓ All events are from Hyderabad!")
            elif non_hyderabad_count > 0:
                logger.warning(f"\n   ✗ Found {non_hyderabad_count} events from other locations!")
            
            # Check optional fields
            logger.info("\n6. Checking optional metadata fields...")
            optional_fields = ['event_language', 'event_type', 'duration', 'event_time', 'event_format', 'attending', 'rating']
            field_coverage = {field: 0 for field in optional_fields}
            
            for event in events:
                for field in optional_fields:
                    if event.get(field) and event.get(field) != '-':
                        field_coverage[field] += 1
            
            for field, count in field_coverage.items():
                pct = 100 * count // len(events) if events else 0
                status = "✓" if count > 0 else "○"
                logger.info(f"   {status} {field}: {count}/{len(events)} ({pct}%)")
            
            logger.info("\n" + "=" * 80)
            logger.info("CONCLUSION")
            logger.info("=" * 80)
            
            if len(events) > 0 and non_hyderabad_count == 0:
                logger.info("\n✓ DISTRICT AGENT IS WORKING CORRECTLY!")
                logger.info(f"  Successfully returned {len(events)} verified Hyderabad events")
                logger.info("\n  Next steps:")
                logger.info("  1. Increase target_count to 150-170 for production")
                logger.info("  2. Verify output matches dashboard and Excel export requirements")
                logger.info("  3. Deploy to production")
                return True
            else:
                logger.error("\n✗ DISTRICT AGENT HAS ISSUES!")
                if len(events) == 0:
                    logger.error("  - No events returned")
                if non_hyderabad_count > 0:
                    logger.error(f"  - Found {non_hyderabad_count} non-Hyderabad events")
                return False
                
        except Exception as e:
            logger.error(f"\n✗ Error during scraping: {e}")
            logger.error(f"   Exception type: {type(e).__name__}")
            import traceback
            logger.error("\n   Full traceback:")
            for line in traceback.format_exc().split('\n'):
                logger.error(f"   {line}")
            return False
    
    except ImportError as e:
        logger.error(f"✗ Failed to import agent: {e}")
        return False
    except Exception as e:
        logger.error(f"✗ Unexpected error: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False

if __name__ == "__main__":
    try:
        result = asyncio.run(test_district_agent_live())
        sys.exit(0 if result else 1)
    except KeyboardInterrupt:
        logger.info("\nTest interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        import traceback
        logger.error(traceback.format_exc())
        sys.exit(1)
