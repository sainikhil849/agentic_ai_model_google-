import asyncio
import logging
from agents.platforms import SkillboxAgent

logging.basicConfig(level=logging.INFO)

async def main():
    agent = SkillboxAgent()
    
    print("\n--- Testing Hyderabad ---")
    hyd_events = await agent.extract_events("Hyderabad", target_count=5)
    print(f"Found {len(hyd_events)} events for Hyderabad")
    for e in hyd_events[:3]:
        print(e)
        
    print("\n--- Testing Mumbai ---")
    mum_events = await agent.extract_events("Mumbai", target_count=5)
    print(f"Found {len(mum_events)} events for Mumbai")
    for e in mum_events[:3]:
        print(e)

if __name__ == "__main__":
    asyncio.run(main())
