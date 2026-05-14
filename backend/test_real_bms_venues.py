"""
Test with actual BookMyShow-like event data to debug "Not specified" issue
"""
import sys
import io

if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

from agents.platforms import BookMyShowAgent

agent = BookMyShowAgent()

# Simulate what BookMyShow detail page might extract
test_events = [
    {
        "name": "Pottery Workshop at Heart Cup Coffee",
        "url": "https://in.bookmyshow.com/events/pottery-workshop",
        "date": "2026-04-19",
        "price": "500",
        "description": "Learn pottery making from expert artisans",
        "location": "Hyderabad",
        "organizer": "Art Academy",
        # Venue as list with full JSON-LD Place
        "venue": [
            {
                "@type": "Place",
                "name": "Heart Cup Coffee: Gachibowli",
                "address": {
                    "@type": "PostalAddress",
                    "addressCountry": "India",
                    "addressLocality": "Hyderabad",
                    "streetAddress": "Old Mumbai Highway, Gachibowli, Hyderabad, Telangana 500032"
                }
            }
        ]
    },
    {
        "name": "Music Workshop",
        "url": "https://in.bookmyshow.com/events/music",
        "date": "2026-04-25",
        "price": "1000",
        "description": "Learn music",
        "location": "Hyderabad",
        # Venue as dict (not list)
        "venue": {
            "@type": "Place",
            "name": "Music Academy: Kondapur",
            "address": {
                "@type": "PostalAddress",
                "addressCountry": "India",
                "addressLocality": "Hyderabad",
                "streetAddress": "3rd Floor, Sangeetha Landmark, Kondapur, Hyderabad, Telangana 500084"
            }
        }
    },
    {
        "name": "Dance Class",
        "url": "https://in.bookmyshow.com/events/dance",
        "date": "2026-04-26",
        "price": "750",
        "description": "Learn dance",
        "location": "Hyderabad",
        # Venue as string only (extraction might have failed)
        "venue": "Dance Studio Hyderabad"
    },
    {
        "name": "Yoga Session",
        "url": "https://in.bookmyshow.com/events/yoga",
        "date": "2026-04-27",
        "price": "300",
        "description": "Yoga class",
        "location": "Hyderabad",
        # No venue at all
    },
]

print("\n" + "="*80)
print("BOOKMYSHOW EVENT VENUE TEST - Debugging 'Not specified'")
print("="*80 + "\n")

for event in test_events:
    print(f"Event: {event['name']}")
    print("-" * 80)
    
    venue_input = event.get("venue")
    print(f"Input venue: {venue_input}")
    print(f"Input venue type: {type(venue_input).__name__}\n")
    
    formatted = agent._format_event(event)
    
    if formatted:
        venue_output = formatted.get("venue", "MISSING")
        print(f"✅ Event formatted")
        print(f"Output venue: {venue_output}")
        
        if venue_output == "Not specified":
            print(f"⚠️  ISSUE: Venue is 'Not specified'\n")
        else:
            print(f"✅ Venue has proper value\n")
    else:
        print(f"❌ Event filtered or failed\n")

