python3 - <<'PY'
p='/vol1/@appcenter/vehicle-mgr/后端/后台管理/index.html'
s=open(p,encoding='utf-8').read()
# Fix accidental literal newline inside JS string: t.split(' newline ')
s=s.replace("t.split('\n').filter", "t.split('\\n').filter")
# If the file contains an actual newline between the quotes, fix that too
s=s.replace("t.split('\n').filter".replace('\\n','\n'), "t.split('\\n').filter")
# Fix vehicle onclick quoting after previous broken replacement
s=s.replace('onclick="editVeh(\\\'+v.plate_number+\\\')"', 'onclick="editVeh(\\\\\'\'+v.plate_number+\'\\\\\')"')
s=s.replace('onclick="delVeh(\\\'+v.plate_number+\\\')"', 'onclick="delVeh(\\\\\'\'+v.plate_number+\'\\\\\')"')
s=s.replace('onclick="doEditVeh(\\\'+v.plate_number+\\\')"', 'onclick="doEditVeh(\\\\\'\'+v.plate_number+\'\\\\\')"')
# Direct fix for the exact bad text currently present
s=s.replace('onclick="editVeh(\\\'+v.plate_number+\\\')"', 'onclick="editVeh(\\\\\'\'+v.plate_number+\'\\\\\')"')
open(p,'w',encoding='utf-8').write(s)
print('fix2 done')
PY
