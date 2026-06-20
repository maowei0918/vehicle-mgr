python3 - <<'PY'
p='/vol1/@appcenter/vehicle-mgr/后端/后台管理/index.html'
s=open(p,encoding='utf-8').read()
s=s.replace("onclick=\"editVeh(''+v.plate_number+'')\"", "onclick=\"editVeh(\\\'"+"+v.plate_number+"+"\\\')\"")
s=s.replace("onclick=\"delVeh(''+v.plate_number+'')\"", "onclick=\"delVeh(\\\'"+"+v.plate_number+"+"\\\')\"")
s=s.replace("onclick=\"doEditVeh(''+v.plate_number+'')\"", "onclick=\"doEditVeh(\\\'"+"+v.plate_number+"+"\\\')\"")
open(p,'w',encoding='utf-8').write(s)
print('fixed vehicle quote bug')
PY
python3 - <<'PY'
import re, subprocess, tempfile, os
p='/vol1/@appcenter/vehicle-mgr/后端/后台管理/index.html'
s=open(p,encoding='utf-8').read()
m=re.search(r'<script>(.*)</script>', s, re.S)
js=m.group(1) if m else ''
fd,path=tempfile.mkstemp(suffix='.js')
os.write(fd, js.encode('utf-8'))
os.close(fd)
r=subprocess.run(['node','--check',path],capture_output=True,text=True)
print(r.stdout+r.stderr)
print('rc',r.returncode)
os.unlink(path)
PY
