import asyncio
import sys
import io
import json

if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

from agents.platforms import get_platform_agent

async def test_optional_fields():
    """Test that optional metadata fields are being extracted."""
    print("\n" + "="*70)
    print("OPTIONAL FIELDS VERIFICATION TEST")
    print("="*70 + "\n")
    
    platforms_to_test = [
        ("District", 3),
        ("BookMyShow", 2),
        ("Meetup", 2),
    ]
    
    for platform_name, count in platforms_to_test:
        print(f"\n[{platform_name}] Testing optional fields extraction...")
        agent = get_platform_agent(platform_name, "Hyderabad")
        
        if not agent:
            print(f"  ERROR: No agent found")
            continue
        
        try:
            events = await agent.extract_events("Hyderabad", count)
            
            if not events:
                print(f"  FAIL: No events returned")
                continue
            
            print(f"  Found {len(events)} events\n")
            
            for i, ev in enumerate(events[:2], 1):
                print(f"  Event {i}: {ev.get('event_name', 'N/A')[:50]}")
                print(f"    Required fields:")
                print(f"      - event_date: {ev.get('event_date', 'MISSING')}")
                print(f"      - price: {ev.get('price', 'MISSING')}")
                print(f"      - organizer: {ev.get('organizer', 'MISSING')}")
                print(f"      - platform: {ev.get('platform', 'MISSING')}")
                
                optional_fields = ['event_language', 'event_type', 'duration', 'event_time', 'event_format', 'attending', 'rating']
                has_optional = False
                print(f"    Optional fields:")
                for field in optional_fields:
                    if field in ev and ev[field]:
                        print(f"      ✓ {field}: {ev[field]}")
                        has_optional = True
                    else:
                        print(f"      - {field}: (not extracted)")
                
                if not has_optional:
                    print(f"    WARNING: No optional fields extracted for this event")
                print()
        
        except Exception as exc:
            print(f"  ERROR: {exc}")
    
    print("\n" + "="*70)
    print("VERIFICATION COMPLETE")
    print("="*70 + "\n")

if __name__ == "__main__":
    asyncio.run(test_optional_fields())
