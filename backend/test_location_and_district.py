#!/usr/bin/env python3
"""
Complete test: Location Validation + District Agent + Event Name & Venue Extraction
Verifies the complete flow from raw input to confirmed location to 5 events with proper data
"""

import asyncio
import sys
import logging

# Windows fix
if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

from utils.location_validator import normalize_location, validate_location, get_location_with_confirmation
from agents.platforms import DistrictAgent

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(levelname)s | %(message)s'
)
logger = logging.getLogger(__name__)

def test_location_validation():
    """Test location normalization and validation"""
    print("\n" + "="*70)
    print("STEP 1: LOCATION VALIDATION TEST")
    print("="*70)
    
    test_cases = [
        "karnataka",
        "bangalore",
        "mumbai",
        "delhi ncr",
        "telangana",
        "Hyderabad",
        "Invalid City XYZ",
    ]
    
    all_pass = True
    
    for user_input in test_cases:
        print(f"\n📍 Input: '{user_input}'")
        
        # Normalize
        normalized, is_valid = normalize_location(user_input)
        print(f"   → Normalized: '{normalized}'")
        
        # Validate
        is_supported, msg = validate_location(normalized)
        print(f"   → Status: {msg}")
        
        if is_supported:
            print(f"   ✓ VALID")
        else:
            print(f"   ✗ INVALID")
            all_pass = False
    
    return all_pass


async def test_district_extraction():
    """Test District agent with confirmed location"""
    print("\n" + "="*70)
    print("STEP 2: DISTRICT AGENT EXTRACTION TEST (5 EVENTS)")
    print("="*70)
    
    # Test with different confirmed locations
    test_locations = ["Hyderabad", "Bangalore", "Mumbai"]
    
    for city in test_locations:
        print(f"\n🔍 Extracting events from: {city}")
        print("-" * 70)
        
        agent = DistrictAgent()
        
        try:
            events = await agent.extract_events(
                location=city,
                target_count=5,
                max_price=None
            )
            
            if not events:
                print(f"❌ No events found for {city}")
                continue
            
            print(f"✓ Found {len(events)} events\n")
            
            # Display each event
            has_all_data = True
            for i, event in enumerate(events, 1):
                event_name = event.get('event_name', 'MISSING!')
                venue = event.get('venue', 'MISSING!')
                date = event.get('event_date', 'N/A')
                price = event.get('price', 'N/A')
                
                print(f"   {i}. {event_name[:50]}")
                print(f"      Venue: {venue[:50]}")
                print(f"      Date: {date} | Price: {price}")
                
                # Check data quality
                if event_name in ['MISSING!', 'Unknown', 'None']:
                    print(f"      ⚠️  MISSING EVENT NAME!")
                    has_all_data = False
                
                if venue in ['MISSING!', 'Not specified', 'None']:
                    print(f"      ⚠️  MISSING VENUE!")
                    has_all_data = False
                
                print()
            
            if has_all_data:
                print(f"✅ {city}: All events have EVENT NAME and VENUE!")
            else:
                print(f"❌ {city}: Some events missing data!")
            
        except Exception as e:
            print(f"❌ Error extracting from {city}: {e}")
            import traceback
            traceback.print_exc()


async def main():
    """Run complete validation and extraction flow"""
    print("\n" + "█"*70)
    print("█  COMPLETE LOCATION + DISTRICT EXTRACTION TEST")
    print("█"*70)
    
    # Test 1: Location Validation
    validation_pass = test_location_validation()
    
    # Test 2: District Extraction
    print("\n" + "="*70)
    await test_district_extraction()
    
    # Summary
    print("\n" + "█"*70)
    print("█  TEST COMPLETE")
    print("█"*70 + "\n")
    
    if validation_pass:
        print("✅ Location Validation: PASS")
    else:
        print("❌ Location Validation: FAIL")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except Exception as e:
        print(f"❌ FATAL ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
