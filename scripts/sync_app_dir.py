import shutil
from pathlib import Path

src = Path('/vol1/@appcenter/vehicle-mgr/后端')
dst = Path('/vol2/1000/AI/车辆管理-飞牛/app/后端')

# sync backend files
files = ['main.py', 'database.py', 'config.py', 'requirements.txt']
for f in files:
    s = src / f
    d = dst / f
    if s.exists():
        shutil.copy2(str(s), str(d))
        print(f'OK  {f}')

# sync subdirs
for dname in ['模型', '路由', '服务']:
    sd = src / dname
    dd = dst / dname
    if not sd.exists():
        continue
    if dd.exists():
        for item in dd.iterdir():
            if item.is_file():
                item.unlink()
            elif item.is_dir():
                shutil.rmtree(str(item))
    else:
        dd.mkdir(parents=True, exist_ok=True)
    for item in sd.iterdir():
        if item.is_file():
            shutil.copy2(str(item), str(dd / item.name))
            print(f'OK  {dname}/{item.name}')

# webadmin
wd = src / '后台管理'
wdd = dst / '后台管理'
if wd.exists():
    if wdd.exists():
        for item in wdd.iterdir():
            if item.is_file():
                item.unlink()
    else:
        wdd.mkdir(parents=True, exist_ok=True)
    for item in wd.iterdir():
        if item.is_file():
            shutil.copy2(str(item), str(wdd / item.name))
            print(f'OK  webadmin/{item.name}')

# also sync dashboard and contract_part if exists in running instance but not in src
for extra in ['dashboard.py', 'contract_part.py']:
    sp_ = src / '路由' / extra
    dp_ = dst / '路由' / extra
    if sp_.exists():
        shutil.copy2(str(sp_), str(dp_))
        print(f'OK  路由/{extra}')

print('--- app/ synced ---')
