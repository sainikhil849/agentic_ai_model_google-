import requests
import xml.etree.ElementTree as ET
try:
    r = requests.get('https://www.district.in/sitemap.xml', timeout=10)
    print("Sitemap status:", r.status_code)
    try:
        root = ET.fromstring(r.text)
        print("Root tag:", root.tag)
        for child in root[:10]:
            print(child[0].text)
    except Exception as e:
        print("Error parsing XML", e)
        print(r.text[:500])
except Exception as e:
    print("Error fetching", e)
