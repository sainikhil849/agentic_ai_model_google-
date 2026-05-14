import requests
from bs4 import BeautifulSoup

url = "https://www.district.in/search?q=hyderabad"
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko)'
}
response = requests.get(url, headers=headers)
print("Search Status:", response.status_code)
with open('district_search.html', 'w', encoding='utf-8') as f:
    f.write(response.text)
