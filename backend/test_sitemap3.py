import requests
import xml.etree.ElementTree as ET
try:
    r = requests.get('https://www.district.in/events/search-sitemap/event-detail-pages.xml', timeout=10)
    print("Sitemap status:", r.status_code)
    try:
        root = ET.fromstring(r.text)
        print("Root tag:", root.tag)
        count = 0
        for child in root:
            if count < 10:
                print(child[0].text)
            count += 1
        print("Total Event URLs:", count)
    except Exception as e:
        print("Error parsing XML", e)
except Exception as e:
    print("Error fetching", e)
