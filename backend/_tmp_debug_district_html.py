import requests
url='https://www.district.in/events/'
r=requests.get(url, timeout=20)
text=r.text
print('status', r.status_code)
print('application/ld+json', text.count('application/ld+json'))
print('window.__', 'window.__' in text)
print('data-react-helmet', text.count('data-react-helmet'))
print('href_events', text.count('href="/events/"'))
print('href_activities', text.count('href="/activities/"'))
print('script type application/json', text.count('application/json'))
print('bodylen', len(text))
print(text[:1200])
