"""
Debug: Trace why venue is becoming "Not specified"
"""
import sys
import io
import json

if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

from agents.platforms import BookMyShowAgent
from utils.venue_validator import format_venue_for_bookmyshow, extract_venue_from_json_ld

agent = BookMyShowAgent()

# Various venue formats that might cause "Not specified"

test_cases = [
    {
        "name": "Venue as list dict (normal case)",
        "raw_event": {
            "url": "https://in.bookmyshow.com/events/test1",
            "name": "Event 1",
            "date": "2026-04-20",
            "price": "500",
            "description": "Test",
            "location": "Hyderabad",
            "venue": [
                {
                    "@type": "Place",
                    "name": "Third Wave Cafe: Gachibowli",
                    "address": {
                        "@type": "PostalAddress",
                        "addressCountry": "India",
                        "addressLocality": "Hyderabad",
                        "streetAddress": "123 Street, Gachibowli, Hyderabad, Telangana 500032"
                    }
                }
            ]
        }
    },
    {
        "name": "Venue as string",
        "raw_event": {
            "url": "https://in.bookmyshow.com/events/test2",
            "name": "Event 2",
            "date": "2026-04-20",
            "price": "500",
            "description": "Test",
            "location": "Hyderabad",
            "venue": "Some Venue Name"
        }
    },
    {
        "name": "Venue as None",
        "raw_event": {
            "url": "https://in.bookmyshow.com/events/test3",
            "name": "Event 3",
            "date": "2026-04-20",
            "price": "500",
            "description": "Test",
            "location": "Hyderabad",
            "venue": None
        }
    },
    {
        "name": "Venue missing entirely",
        "raw_event": {
            "url": "https://in.bookmyshow.com/events/test4",
            "name": "Event 4",
            "date": "2026-04-20",
            "price": "500",
            "description": "Test",
            "location": "Hyderabad",
        }
    },
]

print("\n" + "="*80)
print("DEBUGGING VENUE 'NOT SPECIFIED' ISSUES")
print("="*80 + "\n")

for test in test_cases:
    print(f"TEST: {test['name']}")
    print("-" * 80)
    
    raw_event = test['raw_event']
    venue_raw = raw_event.get("venue")
    
    print(f"Input venue type: {type(venue_raw).__name__}")
    print(f"Input venue value: {venue_raw}\n")
    
    formatted = agent._format_event(raw_event)
    
    if formatted:
        venue_output = formatted.get("venue", "MISSING")
        print(f"Output venue: {venue_output}")
        print(f"Output venue type: {type(venue_output).__name__}")
        
        if venue_output == "Not specified":
            print("⚠️  WARNING: Venue is 'Not specified'")
        else:
            print("✅ Venue has value")
    else:
        print("❌ Event was filtered or failed to format")
    
    print()
