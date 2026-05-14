import asyncio
import logging
import os
import pandas as pd
from agents.platforms import DistrictAgent

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def verify_multicity_district(city="Bangalore"):
    logger.info(f"VERIFYING DISTRICT AGENT FOR: {city}")
    agent = DistrictAgent()
    
    try:
        # Run scraping for the specified city
        events = await agent.extract_events(location=city, target_count=5)
        
        logger.info(f"✓ Found {len(events)} events for {city}")
        
        # Check if Excel was saved
        if agent.excel_filepath and os.path.exists(agent.excel_filepath):
            logger.info(f"✓ Excel file created: {agent.excel_filepath}")
            
            # Verify columns in Excel
            df = pd.read_excel(agent.excel_filepath)
            required_columns = [
                'Event Name', 'Event Place', 'Venue Place', 'Price', 
                'Description', 'Location', 'Event URL', 'Date', 'Time'
            ]
            
            missing = [col for col in required_columns if col not in df.columns]
            if not missing:
                logger.info("✓ All required columns are present in Excel!")
                logger.info(f"Columns: {df.columns.tolist()}")
            else:
                logger.error(f"✗ Missing columns: {missing}")
                
            # Check content
            if not df.empty:
                logger.info("✓ Excel sample data:")
                print(df[required_columns].head(3).to_string())
            else:
                logger.warning("! Excel is empty")
        else:
            logger.error("✗ Excel file not found!")
            
        return len(events) > 0
    except Exception as e:
        logger.error(f"Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    asyncio.run(verify_multicity_district("Bangalore"))
