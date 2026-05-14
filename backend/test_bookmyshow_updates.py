"""
Test BookMyShow updates:
1. Hyderabad-only filter (events with non-Hyderabad venues excluded)
2. Venue format: "Name, Area, City"
3. Description extraction from detail pages
"""
import sys
import io

if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

from agents.platforms import BookMyShowAgent
from datetime import date

def test_hyderabad_filter_and_venue_format():
    """Test that BookMyShow only shows Hyderabad events with correct venue format."""
    print("\n" + "="*70)
    print("TEST: BookMyShow Hyderabad Filter + Venue Format")
    print("="*70 + "\n")
    
    agent = BookMyShowAgent()
    today = date.today()
    passed = 0
    failed = 0
    
    # TEST 1: Hyderabad venue (Heart Cup Coffee, Gachibowli)
    print("TEST 1: Hyderabad venue - Heart Cup Coffee, Gachibowli")
    print("-" * 60)
    raw_event_hyd = {
        "url": "https://in.bookmyshow.com/events/pottery-workshop",
        "name": "Pottery Workshop",
        "date": "2026-04-19",
        "price": "500",
        "description": "Learn pottery making from experts",
        "location": "Hyderabad",
        "venue": {
            "@type": "Place",
            "name": "Heart Cup Coffee: Gachibowli",
            "address": {
                "@type": "PostalAddress",
                "addressCountry": "India",
                "addressLocality": "Hyderabad",
                "streetAddress": "Old Mumbai Highway, Gachibowli, Hyderabad, Telangana 500032, India"
            }
        }
    }
    
    formatted_hyd = agent._format_event(raw_event_hyd)
    if formatted_hyd:
        print(f"✓ Event NOT filtered (correct)\n")
        venue = formatted_hyd.get("venue", "")
        print(f"  Venue: {venue}")
        
        # Check format: should be "Heart Cup Coffee, Gachibowli, Hyderabad"
        if "Heart Cup Coffee" in venue and "Gachibowli" in venue and "Hyderabad" in venue:
            if ", " in venue and venue.count(", ") >= 2:
                print(f"✓ Venue format correct: 'Name, Area, City'\n")
                passed += 1
            else:
                print(f"✗ Venue format incorrect (should be 'Name, Area, City')\n")
                failed += 1
        else:
            print(f"✗ Venue missing required components\n")
            failed += 1
    else:
        print("✗ Event was filtered out (should NOT be filtered)\n")
        failed += 1
    
    # TEST 2: Non-Hyderabad venue (Mumbai)
    print("TEST 2: Non-Hyderabad venue - Thane, Mumbai")
    print("-" * 60)
    raw_event_mumbai = {
        "url": "https://in.bookmyshow.com/events/comedy-show",
        "name": "Daru Badnaam - Comedy Show",
        "date": "2026-04-24",
        "price": "800",
        "description": "Comedy show by Inder Sahani",
        "location": "Hyderabad",  # Note: scraping location is Hyderabad
        "venue": {
            "@type": "Place",
            "name": "Backspace: Thane",
            "address": {
                "@type": "PostalAddress",
                "addressCountry": "India",
                "addressLocality": "Mumbai",  # But actual venue is in Mumbai
                "streetAddress": "First Floor, Lodha Boulevard Mall, Thane West, Mumbai, Maharashtra 400601, India"
            }
        }
    }
    
    formatted_mumbai = agent._format_event(raw_event_mumbai)
    if not formatted_mumbai:
        print(f"✓ Event FILTERED OUT (correct - venue is Mumbai, not Hyderabad)\n")
        passed += 1
    else:
        print(f"✗ Event NOT filtered (should be filtered - venue is {formatted_mumbai.get('venue', 'unknown')})\n")
        failed += 1
    
    # TEST 3: Bangalore venue (Jaipur)
    print("TEST 3: Non-Hyderabad venue - Jaipur")
    print("-" * 60)
    raw_event_jaipur = {
        "url": "https://in.bookmyshow.com/events/gaurav-gupta-live",
        "name": "Gaurav Gupta Live - India Tour",
        "date": "2026-04-26",
        "price": "1200",
        "description": "Comedy tour by Gaurav Gupta",
        "location": "Hyderabad",
        "venue": {
            "@type": "Place",
            "name": "Maharana Pratap Auditorium: Jaipur",
            "address": {
                "@type": "PostalAddress",
                "addressCountry": "India",
                "addressLocality": "Jaipur",
                "streetAddress": "Bharatiya Vidya Bhavan, K. M. Munshi Marg, Jaipur, Rajasthan 302015, India"
            }
        }
    }
    
    formatted_jaipur = agent._format_event(raw_event_jaipur)
    if not formatted_jaipur:
        print(f"✓ Event FILTERED OUT (correct - venue is Jaipur, not Hyderabad)\n")
        passed += 1
    else:
        print(f"✗ Event NOT filtered (should be filtered)\n")
        failed += 1
    
    # TEST 4: Boulder Hills (known Hyderabad venue)
    print("TEST 4: Known Hyderabad venue - Boulder Hills")
    print("-" * 60)
    raw_event_boulder = {
        "url": "https://in.bookmyshow.com/events/og-tour",
        "name": "OG TOUR INDIA WITH THAMAN",
        "date": "2026-06-06",
        "price": "2500",
        "description": "Live concert by THAMAN",
        "location": "Hyderabad",
        "venue": {
            "@type": "Place",
            "name": "Boulder Hills: Hyderabad",
            "address": {
                "@type": "PostalAddress",
                "addressCountry": "India",
                "addressLocality": "Hyderabad",
                "streetAddress": "Opposite ISB, Gachibowli, Khajaguda, Hyderabad, Telangana 500032, India"
            }
        }
    }
    
    formatted_boulder = agent._format_event(raw_event_boulder)
    if formatted_boulder:
        print(f"✓ Event NOT filtered (correct - venue is Hyderabad)\n")
        venue = formatted_boulder.get("venue", "")
        print(f"  Venue: {venue}")
        
        if "Boulder Hills" in venue and "Hyderabad" in venue:
            print(f"✓ Venue contains Boulder Hills and Hyderabad\n")
            passed += 1
        else:
            print(f"✗ Venue missing required components\n")
            failed += 1
    else:
        print("✗ Event was filtered out (should NOT be filtered)\n")
        failed += 1
    
    # TEST 5: Garage Moto Cafe (Jubilee Hills)
    print("TEST 5: Hyderabad venue - Garage Moto Cafe, Jubilee Hills")
    print("-" * 60)
    raw_event_garage = {
        "url": "https://in.bookmyshow.com/events/the-bads-of-hyd",
        "name": "The Bads of Hyderabad",
        "date": "2026-04-19",
        "price": "0",
        "description": "Comedy show",
        "location": "Hyderabad",
        "venue": {
            "@type": "Place",
            "name": "Garage Moto Cafe: Hyderabad",
            "address": {
                "@type": "PostalAddress",
                "addressCountry": "India",
                "addressLocality": "Hyderabad",
                "streetAddress": "ICRISAT Colony, Jubilee Hills, Hyderabad, Telangana 500045, India"
            }
        }
    }
    
    formatted_garage = agent._format_event(raw_event_garage)
    if formatted_garage:
        print(f"✓ Event NOT filtered (correct)\n")
        venue = formatted_garage.get("venue", "")
        print(f"  Venue: {venue}")
        
        if "Garage Moto Cafe" in venue and ("Jubilee Hills" in venue or "Hyderabad" in venue):
            print(f"✓ Venue format is correct\n")
            passed += 1
        else:
            print(f"✗ Venue missing components\n")
            failed += 1
    else:
        print("✗ Event was filtered out (should NOT be filtered)\n")
        failed += 1
    
    # SUMMARY
    print("\n" + "="*70)
    print(f"RESULTS: {passed} passed, {failed} failed")
    print("="*70 + "\n")
    
    return failed == 0


if __name__ == "__main__":
    try:
        success = test_hyderabad_filter_and_venue_format()
        if success:
            print("✅ ALL TESTS PASSED!")
            sys.exit(0)
        else:
            print("❌ SOME TESTS FAILED")
            sys.exit(1)
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
