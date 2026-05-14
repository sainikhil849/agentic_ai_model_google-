"""
Test venue when it comes as a list (the actual problem case)
"""
import sys
import io

if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

from agents.platforms import BookMyShowAgent

agent = BookMyShowAgent()

# THIS IS THE ACTUAL PROBLEM: venue comes as a LIST not a dict
raw_event = {
    "url": "https://in.bookmyshow.com/events/music-dance",
    "name": "Music and Dance Workshop",
    "date": "2026-04-20",
    "price": "1500",
    "description": "Learn music and dance",
    "location": "Hyderabad",
    "organizer": "Academy",
    # IMPORTANT: Venue is a LIST with one dict inside
    "venue": [
        {
            "@type": "Place",
            "name": "Nirvana Music and Dance Academy: Hyderabad",
            "address": {
                "@type": "PostalAddress",
                "addressCountry": "India",
                "addressLocality": "Hyderabad",
                "streetAddress": "3rd Floor, Sangeetha Land Mark, Sri Ram Nagar, Kondapur, Botanical Garden Road, Above Dry Fruits Den, Hyderabad, Telangana 500084, India"
            }
        }
    ]
}

print("Testing venue as LIST format...\n")
print(f"Input venue type: {type(raw_event['venue']).__name__}")
print(f"Input venue: {raw_event['venue']}\n")

formatted = agent._format_event(raw_event)

if formatted:
    print("✅ Event formatted successfully\n")
    
    venue = formatted.get("venue")
    print(f"Output venue: {venue}")
    print(f"Output venue type: {type(venue).__name__}")
    
    if isinstance(venue, str):
        print("\n✅ CORRECT: Venue is a string")
        
        # Check if it's clean format
        if venue.startswith(("-[", "[")):
            print(f"❌ ERROR: Venue still looks like JSON format!")
        elif "Nirvana" in venue and "Kondapur" in venue and "Hyderabad" in venue:
            print(f"✅ CORRECT: Venue format is clean")
            print(f"\nFinal venue: {venue}")
        else:
            print(f"⚠️  Venue format unexpected: {venue}")
    else:
        print(f"❌ ERROR: Venue is {type(venue).__name__}, not string!")
        print(f"Venue value: {venue}")
else:
    print("❌ Event was filtered or failed")
