import json, urllib.request, urllib.error
base='http://localhost:8700'
def req(path, method='GET', data=None, token=None):
    body=json.dumps(data).encode() if data is not None else None
    r=urllib.request.Request(base+path, data=body, method=method)
    r.add_header('Content-Type','application/json')
    if token: r.add_header('Authorization','Bearer '+token)
    try:
        with urllib.request.urlopen(r,timeout=10) as resp:
            return resp.status, resp.read().decode()
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode()
code,body=req('/api/auth/login','POST',{'username':'admin','password':'admin123'})
print('login',code)
token=json.loads(body)['token']
for p in ['/api/contract-parts','/api/repairs','/api/users?role=repair_shop']:
    print(p, req(p, token=token)[0])
