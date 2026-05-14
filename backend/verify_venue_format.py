"""
Verify that the final event dict has venue as simple string, not JSON-LD format
"""
import sys
import io

if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

from agents.platforms import BookMyShowAgent

agent = BookMyShowAgent()

raw_event = {
    "url": "https://in.bookmyshow.com/events/pottery-workshop",
    "name": "Pottery Workshop",
    "date": "2026-04-19",
    "price": "500",
    "description": "Learn pottery",
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

print("Formatting event...")
formatted = agent._format_event(raw_event)

if formatted:
    print("\n✅ Event formatted successfully\n")
    
    venue = formatted.get("venue")
    print(f"Venue value: {venue}")
    print(f"Venue type: {type(venue).__name__}")
    print(f"Venue is string: {isinstance(venue, str)}")
    
    if isinstance(venue, str):
        print(f"\n✅ CORRECT: Venue is a string")
        print(f"Venue format: {venue}")
        
        if venue == "Heart Cup Coffee, Gachibowli, Hyderabad":
            print(f"✅ CORRECT: Venue matches expected format")
        else:
            print(f"⚠️  Venue doesn't match expected format")
            print(f"Expected: Heart Cup Coffee, Gachibowli, Hyderabad")
    elif isinstance(venue, dict):
        print(f"\n❌ PROBLEM: Venue is still a dict!")
        print(f"Venue dict keys: {venue.keys()}")
    elif isinstance(venue, list):
        print(f"\n❌ PROBLEM: Venue is a list!")
        print(f"Venue list: {venue}")
    else:
        print(f"\n⚠️  Venue is unknown type: {type(venue)}")
else:
    print("❌ Event was filtered or formatted to None")
