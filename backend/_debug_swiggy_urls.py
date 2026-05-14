import requests

urls = [
    'https://www.swiggy.com/scenes',
    'https://www.swiggy.com/scenes/hyderabad',
    'https://www.swiggy.com/scenes?city=Hyderabad',
    'https://www.swiggy.com/scenes?city=hyderabad',
    'https://www.swiggy.com/scenes/?city=hyderabad',
    'https://www.swiggy.com/scenes/experiences',
    'https://www.swiggy.com/scenes/experiences?city=Hyderabad',
    'https://www.swiggy.com/scenes/all-events',
]
headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36'}
for u in urls:
    try:
        r = requests.get(u, headers=headers, timeout=20, allow_redirects=True)
        print('\nURL:', u)
        print('Status:', r.status_code, 'Final:', r.url)
        print('Title snippet:', r.text[:300].replace('\n',' '))
    except Exception as e:
        print('\nURL:', u, 'ERROR', e)
