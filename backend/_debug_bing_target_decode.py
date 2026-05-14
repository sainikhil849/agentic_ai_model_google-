import requests, re, urllib.parse, base64

q = 'swiggy scenes hyderabad events'
url = 'https://www.bing.com/search?q=' + requests.utils.quote(q)
headers = {'User-Agent': 'Mozilla/5.0'}
r = requests.get(url, headers=headers, timeout=20)
text = r.text
print('status', r.status_code)
for encoded in re.findall(r'u=([^&\"\']+)', text):
    if not encoded.startswith('a1'):
        continue
    raw = encoded
    decoded = None
    try:
        decoded = base64.b64decode(encoded + '===').decode('utf-8', errors='ignore')
    except Exception:
        decoded = urllib.parse.unquote(encoded)
    clean = decoded
    if clean.startswith('a1'):
        clean = clean[2:]
    print('raw', raw[:120])
    print('decoded', decoded[:200])
    print('clean', clean[:200])
    print('-----')
