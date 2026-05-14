import sys
import asyncio
import logging
import json

if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

from agents.platforms import BookMyShowAgent

# Configure logging to see rejections and scroll progress
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

async def main():
    agent = BookMyShowAgent()
    target = 120
    city = "Delhi"
    
    print(f"\nTesting BookMyShow Yield for {city} (Target: {target})...")
    print("Strictly excluding Gurgaon and Noida as requested.")
    
    events = await agent.extract_events(
        location=city,
        target_count=target,
        max_price=None
    )
    
    print("\n" + "="*80)
    print(f"RESULTS FOR {city}")
    print("="*80)
    print(f"Total events found: {len(events)}")
    
    if events:
        # Verify no Gurgaon/Noida leaked in
        gurgaon_count = sum(1 for e in events if "gurgaon" in str(e.get("venue", "")).lower() or "gurugram" in str(e.get("venue", "")).lower())
        noida_count = sum(1 for e in events if "noida" in str(e.get("venue", "")).lower())
        
        print(f"Gurgaon/Gurugram events: {gurgaon_count} (Should be 0)")
        print(f"Noida events: {noida_count} (Should be 0)")
        
        # Sample check
        print("\nSample Events:")
        for idx, e in enumerate(events[:5], 1):
            print(f"{idx}. {e.get('event_name')} @ {e.get('venue')}")

if __name__ == "__main__":
    asyncio.run(main())
