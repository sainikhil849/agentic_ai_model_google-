import pandas as pd
from pathlib import Path

excel_file = Path("exports/BookMyShow_bangalore_10events_20260419_223322.xlsx")

print("\n" + "="*80)
print("EXCEL FILE ANALYSIS - VENUE & PRICE EXTRACTION")
print("="*80 + "\n")

if not excel_file.exists():
    print(f"✗ File not found: {excel_file}")
else:
    try:
        # Read Excel file
        df = pd.read_excel(excel_file)
        
        print(f"✓ Successfully read Excel file")
        print(f"   File: {excel_file.name}")
        print(f"   Size: {excel_file.stat().st_size} bytes")
        print(f"   Rows: {len(df)}")
        print(f"   Columns: {list(df.columns)}\n")
        
        # Display data
        print("EXTRACTED DATA:")
        print("-" * 80)
        
        for idx, row in df.iterrows():
            print(f"\n[{idx+1}] {row.get('Title', 'N/A')}")
            print(f"    Venue: {row.get('Venue', 'N/A')}")
            print(f"    Price: {row.get('Price', 'N/A')}")
            print(f"    Date: {row.get('Date', 'N/A')}")
            
        # Venue and Price Summary
        print("\n" + "="*80)
        print("VENUE & PRICE SUMMARY")
        print("="*80)
        
        venues_extracted = df["Venue"].notna().sum()
        venues_with_data = (df["Venue"] != "Not specified").sum() if "Venue" in df.columns else 0
        prices_extracted = df["Price"].notna().sum()
        prices_with_value = (df["Price"] != 0).sum() if "Price" in df.columns else 0
        
        print(f"\n✓ Venues extracted: {venues_extracted}/{len(df)}")
        print(f"  - Venues with data: {venues_with_data}")
        print(f"  - 'Not specified' venues: {venues_extracted - venues_with_data}")
        
        print(f"\n✓ Prices extracted: {prices_extracted}/{len(df)}")
        print(f"  - Prices with values: {prices_with_value}")
        print(f"  - Zero/empty prices: {prices_extracted - prices_with_value}")
        
        # Sample venue and price values
        print(f"\n✓ Sample venues:")
        sample_venues = df["Venue"].dropna().unique()[:5]
        for venue in sample_venues:
            if venue != "Not specified":
                print(f"  - {venue}")
        
        print(f"\n✓ Sample prices:")
        sample_prices = df["Price"].dropna().unique()[:5]
        for price in sample_prices:
            if price != 0:
                print(f"  - {price}")
        
    except Exception as e:
        print(f"✗ Error reading Excel file: {e}")
        import traceback
        traceback.print_exc()

print("\n" + "="*80 + "\n")
