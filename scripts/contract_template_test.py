import json, urllib.request, urllib.error
base='http://localhost:8700'
def req(path, method='GET', data=None, token=None, limit=None):
    body=json.dumps(data).encode() if data is not None else None
    r=urllib.request.Request(base+path, data=body, method=method)
    r.add_header('Content-Type','application/json')
    if token: r.add_header('Authorization','Bearer '+token)
    try:
        with urllib.request.urlopen(r,timeout=10) as resp:
            b=resp.read(limit) if limit else resp.read()
            return resp.status, b
    except urllib.error.HTTPError as e:
        return e.code, e.read()
code,body=req('/api/auth/login','POST',{'username':'admin','password':'admin123'})
print('login',code)
token=json.loads(body.decode())['token']
for p in ['/api/contract-parts/template.xlsx','/api/contract-parts','/api/contract-parts/models']:
    print(p, req(p, token=token, limit=64)[0])
