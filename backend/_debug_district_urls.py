import requests

urls = [
    'https://www.district.in/',
    'https://www.district.in/events-in-hyderabad/',
    'https://www.district.in/hyderabad-events',
    'https://www.district.in/events/hyderabad',
    'https://www.district.in/hyderabad',
    'https://www.district.in/api/events?city=hyderabad',
]
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36'
}
for u in urls:
    try:
        r = requests.get(u, headers=headers, timeout=20, allow_redirects=True)
        print('\nURL:', u)
        print('Status:', r.status_code)
        print('Final URL:', r.url)
        print('Content starts:', r.text[:500].replace('\n',' '))
    except Exception as e:
        print('\nURL:', u, 'ERROR', e)
