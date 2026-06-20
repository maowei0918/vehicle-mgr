python3 - <<'PY'
p='/vol1/@appcenter/vehicle-mgr/后端/后台管理/index.html'
s=open(p,encoding='utf-8').read()
s=s.replace("t.split('\n').filter", "t.split('\\n').filter")
open(p,'w',encoding='utf-8').write(s)
print('newline fixed')
PY
