import requests
import re

q = 'swiggy scenes hyderabad events'
url = 'https://www.bing.com/search?q=' + requests.utils.quote(q)
headers = {'User-Agent': 'Mozilla/5.0'}
r = requests.get(url, headers=headers, timeout=20)
text = r.text
print('status', r.status_code)
print('swiggy count', text.lower().count('swiggy'))
print('b_algo count', text.count('class="b_algo"'))
for idx in [m.start() for m in re.finditer('class="b_algo"', text)][:5]:
    print('b_algo chunk at', idx)
    print(text[idx:idx+1200].replace('\n',' '))
links = re.findall(r'href=\"(https?://[^\"]+)\"', text)
print('total links', len(links))
sw = [l for l in links if 'swiggy' in l.lower()]
print('swiggy links', sw[:20])
