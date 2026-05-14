import requests

url = "https://www.district.in/events"
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
}

response = requests.get(url, headers=headers)
with open('district_source.html', 'w', encoding='utf-8') as f:
    f.write(response.text)
print("Saved HTML")
