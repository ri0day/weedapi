import requests
import json
sig_url = 'http://10.0.31.15:80/auth'
d={"username":"user2","password":"abcxyz"}
headers = {'content-type': 'application/json'}

def get_token(sig_url):
    r = requests.post(sig_url,data=json.dumps(d),headers = headers)
    access_token = r.json()['access_token']
    return access_token

sig_header = {'Authorization': 'JWT '+ get_token(sig_url)}

filename='/var/log/dmesg'

files={'Filedata':open(filename,'rb')}

print 'end header'
r = requests.post('http://10.0.31.15:80/upload',files=files,headers=sig_header)
print r.headers,r.status_code,r.text
