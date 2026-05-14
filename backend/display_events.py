import pandas as pd

df = pd.read_excel('exports/DISTRICT_LIVE_20260417_184307.xlsx')

print('FILE: DISTRICT_LIVE_20260417_184307.xlsx')
print('='*90)
print(f'Total Rows: {len(df)} | Total Columns: {len(df.columns)}')
print('\nCOLUMN HEADERS:')
for i, col in enumerate(df.columns, 1):
    print(f'  {i:2d}. {col}')

print('\n' + '='*90)
print('EVENT DATA (All 10 Rows):')
print('='*90)

for idx, row in df.iterrows():
    print(f'\nRow {idx+1}:')
    print(f'  Event Name:  {row["Event Name"]}')
    print(f'  Date:        {row["Date"]}')
    print(f'  Time:        {row["Time"]}')
    print(f'  Price:       {row["Price"]}')
    print(f'  Platform:    {row["Platform"]}')
    print(f'  Location:    {row["Location"]}')
    print(f'  Venue:       {row["Venue"]}')
    print(f'  Organizer:   {row["Organizer"]}')
    print(f'  Language:    {row["Language"]}')
    print(f'  Type:        {row["Type"]}')
    print(f'  Format:      {row["Format"]}')
    print(f'  Link:        {row["Link"]}')
