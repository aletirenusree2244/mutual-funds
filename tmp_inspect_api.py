import requests

url = 'https://api.mfapi.in/mf/125497'
response = requests.get(url, timeout=15)
print('status', response.status_code)
print(response.text[:2000])
