import pandas as pd
from pathlib import Path

excel_file = Path("exports/BookMyShow_bangalore_10events_20260419_223322.xlsx")

print("\n" + "="*80)
print("DETAILED EXCEL CONTENT - ALL COLUMNS")
print("="*80 + "\n")

try:
    df = pd.read_excel(excel_file)
    
    # Display full DataFrame
    print("Full DataFrame content:\n")
    print(df.to_string())
    
    print("\n\n" + "="*80)
    print("COLUMN DETAILS")
    print("="*80 + "\n")
    
    for col in df.columns:
        print(f"Column: {col}")
        print(f"  Data type: {df[col].dtype}")
        print(f"  Non-null count: {df[col].notna().sum()}/{len(df)}")
        print(f"  Sample values: {df[col].dropna().head(2).tolist()}")
        print()
    
    print("\n" + "="*80)
    print("VENUE EXTRACTION QUALITY CHECK")
    print("="*80 + "\n")
    
    venues = df["Venue"].tolist()
    print(f"All venues extracted:\n")
    for i, venue in enumerate(venues, 1):
        print(f"{i:2}. {venue}")
    
    print("\n" + "="*80)
    print("PRICE EXTRACTION QUALITY CHECK")
    print("="*80 + "\n")
    
    prices = df["Price"].tolist()
    print(f"All prices extracted:\n")
    for i, price in enumerate(prices, 1):
        print(f"{i:2}. {price} (Type: {type(price).__name__})")
    
except Exception as e:
    print(f"✗ Error: {e}")
    import traceback
    traceback.print_exc()

print("\n")
