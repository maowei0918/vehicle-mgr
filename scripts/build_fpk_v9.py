import zipfile, os
from pathlib import Path

base = Path('/vol2/1000/AI/车辆管理-飞牛')
out = base / 'vehicle-mgr-v9.fpk'

# version bump in manifest
manifest = base / 'manifest'
m = manifest.read_text(encoding='utf-8')
m = m.replace('version               = 1.0.0', 'version               = 9.0.0')
manifest.write_text(m, encoding='utf-8')

with zipfile.ZipFile(str(out), 'w', zipfile.ZIP_DEFLATED) as zf:
    for root, dirs, files in os.walk(str(base)):
        root = Path(root)
        # skip old fpk files and __pycache__
        dirs[:] = [d for d in dirs if d != '__pycache__' and not d.endswith('.fpk')]
        for f in files:
            if f.endswith('.fpk'):
                continue
            full = root / f
            arcname = full.relative_to(base)
            zf.write(str(full), str(arcname))
            print(f'  {arcname}')

print(f'\nOK  {out.name}  ({out.stat().st_size} bytes)')
