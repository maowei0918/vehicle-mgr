#!/usr/bin/env python3
"""Fix symlink targets inside a vehicle-mgr fpk file.

The fnpack build tool corrupts symlinks like:
  backend/models -> models   (should be -> 模型)
  backend/routers -> routers  (should be -> 路由)
  backend/services -> services (should be -> 服务)

This script reads an existing fpk, fixes the symlinks in the embedded
app.tgz, and writes a corrected fpk.
"""

import gzip
import io
import os
import sys
import tarfile

SYMLINK_FIXES = {
    '后端/models': '模型',
    '后端/routers': '路由',
    '后端/services': '服务',
}


def fix_fpk(input_path: str, output_path: str) -> None:
    # Read input fpk (gzip-compressed tar)
    with gzip.open(input_path, 'rb') as f:
        fpk_data = f.read()

    outer = tarfile.open(fileobj=io.BytesIO(fpk_data))

    members = []  # list of (TarInfo, bytes|None)
    for m in outer.getmembers():
        if m.name == 'app.tgz':
            # Extract and fix the inner app.tgz
            app_tgz_data = outer.extractfile('app.tgz').read()
            inner_in = tarfile.open(fileobj=io.BytesIO(app_tgz_data))

            inner_buf = io.BytesIO()
            inner_out = tarfile.open(fileobj=inner_buf, mode='w:gz')

            fixed_count = 0
            for im in inner_in.getmembers():
                if im.issym() and im.name in SYMLINK_FIXES:
                    old_target = im.linkname
                    new_target = SYMLINK_FIXES[im.name]
                    print(f"  Fixing: {im.name} -> {old_target}  ===>  {new_target}")
                    im.linkname = new_target
                    fixed_count += 1
                inner_out.addfile(
                    im,
                    inner_in.extractfile(im) if not im.isdir() else None,
                )

            inner_out.close()
            fixed_app_tgz = inner_buf.getvalue()

            # Update the member's size in the outer tar
            m.size = len(fixed_app_tgz)
            members.append((m, fixed_app_tgz))
            print(f"  Fixed {fixed_count} symlinks in app.tgz")
        else:
            data = outer.extractfile(m).read() if not m.isdir() else None
            members.append((m, data))

    outer.close()

    # Write output fpk
    out_buf = io.BytesIO()
    outer_out = tarfile.open(fileobj=out_buf, mode='w:gz')
    for m, data in members:
        outer_out.addfile(m, io.BytesIO(data) if data else None)
    outer_out.close()

    with open(output_path, 'wb') as f:
        f.write(out_buf.getvalue())

    print(f"\nDone! Output: {output_path}")
    print(f"Size: {os.path.getsize(output_path)} bytes")

    # Verify
    print("\nVerifying fixed symlinks:")
    with gzip.open(output_path, 'rb') as f:
        verify_data = f.read()
    verify_outer = tarfile.open(fileobj=io.BytesIO(verify_data))
    verify_inner_data = verify_outer.extractfile('app.tgz').read()
    verify_inner = tarfile.open(fileobj=io.BytesIO(verify_inner_data))
    for vm in verify_inner.getmembers():
        if vm.issym():
            print(f"  {vm.name} -> {vm.linkname}")
    verify_inner.close()
    verify_outer.close()


if __name__ == '__main__':
    if len(sys.argv) != 3:
        print(f"Usage: {sys.argv[0]} <input.fpk> <output.fpk>")
        sys.exit(1)

    fix_fpk(sys.argv[1], sys.argv[2])
