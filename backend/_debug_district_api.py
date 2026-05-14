import requests

url = 'https://mpc-prod-24-s6uit34pua-uw.a.run.app/events?cee=no'
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36',
    'Accept': 'application/json, text/plain, */*'
}
try:
    r = requests.get(url, headers=headers, timeout=30)
    print('status', r.status_code)
    print('content-type', r.headers.get('content-type'))
    txt = r.text[:1000]
    print('body snippet', txt)
    import json
    data = r.json()
    if isinstance(data, dict):
        print('keys', data.keys())
        print('len', len(data))
    else:
        print('type', type(data), 'len', len(data))
except Exception as e:
    print('error', e)
