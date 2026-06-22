import tarfile, os, hashlib, zipfile, re
from pathlib import Path

base = Path('/vol2/1000/AI/车辆管理-飞牛')
app_dir = base / 'app'
out_fpk = base / 'vehicle-mgr-beta14.fpk'

# 1) rebuild app.tgz from app/ dir
tgz_path = base / 'app.tgz'
with tarfile.open(str(tgz_path), 'w:gz') as tar:
    for root, dirs, files in os.walk(str(app_dir), followlinks=False):
        root_path = Path(root)
        for f in files:
            full = root_path / f
            if full.is_symlink():
                arcname = full.relative_to(app_dir)
                tar.add(str(full), str(arcname), recursive=False)
            else:
                arcname = full.relative_to(app_dir)
                tar.add(str(full), str(arcname))
        for d in list(dirs):
            full = root_path / d
            if full.is_symlink():
                arcname = full.relative_to(app_dir)
                tar.add(str(full), str(arcname), recursive=False)
                dirs.remove(d)

sz = tgz_path.stat().st_size
print(f'app.tgz: {sz} bytes ({sz/1024/1024:.1f} MB)')

# 2) verify symlinks
print('\nSymlinks in app.tgz:')
with tarfile.open(str(tgz_path), 'r:gz') as tf:
    for m in tf.getmembers():
        if m.issym():
            print(f'  {m.name} -> {m.linkname}')

# 3) compute checksum
sha256 = hashlib.sha256()
with open(str(tgz_path), 'rb') as f:
    for chunk in iter(lambda: f.read(65536), b''):
        sha256.update(chunk)
checksum = sha256.hexdigest()

# 4) update manifest version + checksum
manifest_path = base / 'manifest'
manifest_text = manifest_path.read_text(encoding='utf-8')
manifest_text = re.sub(r'version\s*=\s*[\d.]+', 'version               = 14.0.0', manifest_text)
manifest_text = re.sub(r'checksum\s*=.*', '', manifest_text)
manifest_text = manifest_text.strip() + f'\nchecksum              = {checksum}\n'
manifest_path.write_text(manifest_text, encoding='utf-8')

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
    for icon in ['ICON.PNG', 'ICON_256.PNG', '.gitignore']:
        icon_path = base / icon
        if icon_path.exists():
            zf.write(str(icon_path), icon)

print(f'\nOK  {out_fpk.name}  ({out_fpk.stat().st_size / 1024 / 1024:.1f} MB)')
