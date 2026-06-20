from pathlib import Path
import shutil, os, stat

src = Path('/vol1/@appcenter/vehicle-mgr/后端')  # running instance (latest code)
dst = Path('/vol2/1000/AI/车辆管理-飞牛/程序/后端')  # fpk source

# files to sync (relative to backend/)
files = [
    'main.py',
    'database.py',
    'config.py',
    'requirements.txt',
]

for f in files:
    s = src / f
    d = dst / f
    if s.exists():
        shutil.copy2(str(s), str(d))
        print(f'OK  {f}')

# dirs to sync fully
for dname in ['模型', '路由', '服务']:
    sd = src / dname
    dd = dst / dname
    if not sd.exists():
        continue
    # clear dest dir
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
        elif item.is_dir():
            shutil.copytree(str(item), str(dd / item.name))
            print(f'OK  {dname}/{item.name}/')

# webadmin (frontend)
wd = src / '后台管理'
wdd = dst / 'webadmin'
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

print('--- sync complete ---')
