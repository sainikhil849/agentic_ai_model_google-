import requests
import json
import re
from bs4 import BeautifulSoup

url = "https://www.district.in/events"
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
}

response = requests.get(url, headers=headers)
print("Status Code:", response.status_code)

soup = BeautifulSoup(response.text, 'html.parser')
next_data = soup.find('script', id='__NEXT_DATA__')

if next_data:
    data = json.loads(next_data.string)
    
    # Save to file to analyze
    with open('district_test.json', 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2)
    print("Saved __NEXT_DATA__ to district_test.json")
    
    # Let's count events
    events_found = []
    
    def find_events(obj):
        if isinstance(obj, dict):
            if obj.get('eventName') or obj.get('name'):
                events_found.append(obj.get('eventName') or obj.get('name'))
            for v in obj.values():
                find_events(v)
        elif isinstance(obj, list):
            for i in obj:
                find_events(i)
                
    find_events(data)
    print(f"Total events found in __NEXT_DATA__: {len(events_found)}")
    if len(events_found) > 0:
        print("Sample:", events_found[:5])
else:
    print("__NEXT_DATA__ not found")
