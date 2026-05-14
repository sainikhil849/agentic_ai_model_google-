
import pandas as pd
import os

filepath = "exports/events-Hyderabad-bookmyshow.xlsx"
if os.path.exists(filepath):
    df = pd.read_excel(filepath)
    print("Columns:", df.columns.tolist())
    print("\nFirst row data:")
    print(df.iloc[0].to_dict())
else:
    print(f"File {filepath} not found.")
