p='/vol1/@appcenter/vehicle-mgr/后端/后台管理/index.html'
s=open(p,encoding='utf-8').read()
s=s.replace("onclick=\"editVeh(''+v.plate_number+'')\"", "onclick=\"editVeh(\\\'"+"+v.plate_number+"+"\\\')\"")
s=s.replace("onclick=\"delVeh(''+v.plate_number+'')\"", "onclick=\"delVeh(\\\'"+"+v.plate_number+"+"\\\')\"")
s=s.replace("onclick=\"doEditVeh(''+v.plate_number+'')\"", "onclick=\"doEditVeh(\\\'"+"+v.plate_number+"+"\\\')\"")
open(p,'w',encoding='utf-8').write(s)
print('done')
