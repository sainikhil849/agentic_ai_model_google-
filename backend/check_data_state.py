"""Check current data state"""
import json
import os

os.chdir(r'c:\Users\saini\OneDrive\Desktop\codes\New folder\exports')

files = [f for f in os.listdir('.') if 'district' in f and '.json' in f and 'real' in f]
print('Files in exports:')
for f in files:
    size = os.path.getsize(f)
    print(f'  ✓ {f} ({size:,} bytes)')

if os.path.exists('district_events_real_data.json'):
    with open('district_events_real_data.json', 'r', encoding='utf-8') as file:
        data = json.load(file)
    
    print('\n✓ DATA LOADED:')
    total = 0
    for city in ['Mumbai', 'Delhi', 'Chennai', 'Pune']:
        if city in data:
            events = data[city]
            total += len(events)
            status = "✓" if len(events) > 0 else "✗"
            print(f'  {status} {city}: {len(events)} events')
            
            if events:
                e = events[0]
                print(f'      Sample: {e.get("event_name", "N/A")[:40]}')
                print(f'      URL: {e.get("event_url", "N/A")[:50]}')
    
    print(f'\nTOTAL: {total} REAL EVENTS READY')
    if total > 0:
        print('\n✓✓✓ DATA IS GOOD - READY TO USE ✓✓✓')
else:
    print('NO district_events_real_data.json found!')
