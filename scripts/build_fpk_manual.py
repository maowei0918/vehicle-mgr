import tarfile, os, hashlib, json, io, zipfile
from pathlib import Path

base = Path('/vol2/1000/AI/车辆管理-飞牛')
app_dir = base / 'app'
out_fpk = base / 'vehicle-mgr-beta11.fpk'

# 1) create app.tgz
tgz_path = base / 'app.tgz'
with tarfile.open(str(tgz_path), 'w:gz') as tar:
    for root, dirs, files in os.walk(str(app_dir), followlinks=False):
        root_path = Path(root)
        # add regular files
        for f in files:
            full = root_path / f
            if full.is_symlink():
                # symlink file: add as symlink
                arcname = full.relative_to(app_dir)
                tar.add(str(full), str(arcname), recursive=False)
                print(f'  tgz: {arcname} (symlink -> {os.readlink(str(full))})')
            else:
                arcname = full.relative_to(app_dir)
                tar.add(str(full), str(arcname))
                print(f'  tgz: {arcname}')
        # add symlink dirs (os.walk puts them in dirs list when followlinks=False)
        # but we need to add the symlink itself, not the content
        for d in list(dirs):
            full = root_path / d
            if full.is_symlink():
                arcname = full.relative_to(app_dir)
                tar.add(str(full), str(arcname), recursive=False)
                print(f'  tgz: {arcname}/ (symlink dir -> {os.readlink(str(full))})')
                dirs.remove(d)  # don't descend into it (already followed if needed)

print(f'app.tgz: {tgz_path.stat().st_size} bytes')

# 2) read manifest
manifest_text = (base / 'manifest').read_text(encoding='utf-8')

# 3) compute checksum of app.tgz
sha256 = hashlib.sha256()
with open(str(tgz_path), 'rb') as f:
    for chunk in iter(lambda: f.read(65536), b''):
        sha256.update(chunk)
checksum = sha256.hexdigest()

# 4) update manifest with checksum
manifest_lines = []
for line in manifest_text.splitlines():
    if line.startswith('checksum'):
        continue
    manifest_lines.append(line)
manifest_lines.append(f'checksum              = {checksum}')
manifest_text = '\n'.join(manifest_lines) + '\n'

# 5) create fpk (zip with app.tgz + manifest + cmd/ + config/ + wizard/ + ICON*)
with zipfile.ZipFile(str(out_fpk), 'w', zipfile.ZIP_DEFLATED) as zf:
    zf.write(str(tgz_path), 'app.tgz')
    zf.writestr('app.tgz.sha256', checksum + '\n')
    zf.writestr('manifest', manifest_text)
    
    for subdir_name in ['cmd', 'config', 'wizard']:
        subdir = base / subdir_name
        if subdir.exists():
            for item in subdir.rglob('*'):
                if item.is_file():
                    arcname = item.relative_to(base)
                    zf.write(str(item), str(arcname))
    
    for icon in ['ICON.PNG', 'ICON_256.PNG']:
        icon_path = base / icon
        if icon_path.exists():
            zf.write(str(icon_path), icon)

print(f'\nOK  {out_fpk.name}  ({out_fpk.stat().st_size} bytes)')
print(f'checksum: {checksum}')
