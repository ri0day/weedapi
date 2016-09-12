import requests
r = requests.get('http://10.0.31.15:80/get/2,24aed21df3bd/x.pdf')
print r.headers,r.status_code
