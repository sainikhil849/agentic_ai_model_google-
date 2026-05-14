"""
Final verification: Show exact output format for BookMyShow events
"""
import sys
import io
import json

if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

from agents.platforms import BookMyShowAgent

def show_event_output():
    print("\n" + "="*80)
    print("BOOKMYSHOW FINAL EVENT OUTPUT FORMAT")
    print("="*80 + "\n")
    
    agent = BookMyShowAgent()
    
    # Test case with all details
    raw_event = {
        "url": "https://in.bookmyshow.com/events/pottery-workshop",
        "name": "Pottery Workshop - Learn from Experts",
        "date": "2026-04-19",
        "price": "500",
        "description": "Learn pottery making from local artisans with 20+ years experience",
        "location": "Hyderabad",
        "organizer": "Art Academy",
        "venue": {
            "@type": "Place",
            "name": "Heart Cup Coffee: Gachibowli",
            "address": {
                "@type": "PostalAddress",
                "addressCountry": "India",
                "addressLocality": "Hyderabad",
                "streetAddress": "Old Mumbai Highway, Next to HP Petrol Pump, Venkatadri Fuel Point, Mouryas Ranga Prasad Avenue, Indira Nagar, Gachibowli, Hyderabad, Telangana 500032, India"
            }
        }
    }
    
    formatted = agent._format_event(raw_event)
    
    if formatted:
        print("✅ EVENT SUCCESSFULLY FORMATTED\n")
        print("OUTPUT FORMAT:\n")
        print(f"Event Name: {formatted.get('event_name')}")
        print(f"Date: {formatted.get('event_date')}")
        print(f"Time: {formatted.get('event_time', 'N/A')}")
        print(f"Price: ₹{formatted.get('price')}")
        print(f"Venue: {formatted.get('venue')}")
        print(f"Organizer: {formatted.get('organizer')}")
        print(f"Platform: {formatted.get('platform')}")
        print(f"City: {formatted.get('city')}")
        print(f"Description: {formatted.get('description')}")
        print(f"URL: {formatted.get('event_url')}")
        
        print("\n" + "-"*80)
        print("VENUE DETAILS CHECK:\n")
        venue = formatted.get('venue')
        print(f"Venue Value: {venue}")
        print(f"Venue Type: {type(venue).__name__}")
        print(f"Is String: {isinstance(venue, str)}")
        print(f"Is Dict: {isinstance(venue, dict)}")
        print(f"Is List: {isinstance(venue, list)}")
        
        if isinstance(venue, str):
            print(f"\n✅ CORRECT: Venue is a clean string")
            print(f"   Format: Name, Area, City")
        else:
            print(f"\n❌ ERROR: Venue is {type(venue).__name__}, not string!")
        
        print("\n" + "-"*80)
        print("FULL EVENT DICTIONARY (JSON):\n")
        event_json = json.dumps(formatted, indent=2, default=str)
        print(event_json)
        
        return True
    else:
        print("❌ Event was filtered or formatting failed")
        return False

if __name__ == "__main__":
    success = show_event_output()
    if not success:
        sys.exit(1)
