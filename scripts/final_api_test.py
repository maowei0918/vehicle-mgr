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
print('login', code)
token=json.loads(body)['token']
for p in ['/api/auth/me','/api/users','/api/users/1','/api/groups','/api/users?role=repair_shop','/api/vehicles','/api/repairs']:
    print(p, req(p, token=token)[0])
print('invalid username', req('/api/users','POST',{'username':'abc123','password':'123456','name':'bad','phone':'13800138000','role':'driver'},token=token))
print('short password', req('/api/users','POST',{'username':'abcdef','password':'123','name':'bad','phone':'13800138000','role':'driver'},token=token))
print('bad phone', req('/api/users','POST',{'username':'abcdef','password':'123456','name':'bad','phone':'1111','role':'driver'},token=token))
print('empty import', req('/api/users/import','POST',[],token=token))
