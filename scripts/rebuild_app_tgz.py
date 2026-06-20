#!/usr/bin/env python3
"""重建 app.tgz — 从 app/ 目录重新打包，保留正确符号链接"""
import os, sys, tarfile
from pathlib import Path

APP_DIR = Path(__file__).resolve().parent.parent / "app"
OUTPUT = Path(__file__).resolve().parent.parent / "app.tgz"

def main():
    """重建 app.tgz，正确处理符号链接"""
    if not APP_DIR.is_dir():
        print(f"错误: 找不到 app/ 目录: {APP_DIR}")
        sys.exit(1)

    # 删除旧的 app.tgz
    if OUTPUT.exists():
        os.remove(OUTPUT)
        print(f"已删除旧 {OUTPUT}")

    with tarfile.open(str(OUTPUT), "w:gz") as tf:
        for entry in sorted(APP_DIR.iterdir()):
            tf.add(str(entry), arcname=entry.name, recursive=True)
    
    size_mb = OUTPUT.stat().st_size / 1024 / 1024
    print(f"已生成 {OUTPUT} ({size_mb:.1f} MB)")

    # 验证符号链接
    with tarfile.open(str(OUTPUT), "r:gz") as tf:
        for m in tf.getmembers():
            if m.issym():
                print(f"  symlink: {m.name} -> {m.linkname}")

if __name__ == "__main__":
    main()
