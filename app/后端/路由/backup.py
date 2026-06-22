"""数据备份与恢复"""
import io, json, os, shutil, tarfile
from datetime import datetime
from pathlib import Path
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Query
from fastapi.responses import StreamingResponse, FileResponse
from sqlalchemy.ext.asyncio import AsyncSession
from database import get_db, engine, DATABASE_URL
from models.user import User
from services.auth import get_current_user, require_role

VERSION = "1.0.0"
BACKUP_MAGIC = "vehicle-mgr-backup-v1"

router = APIRouter(prefix="/api/backup", tags=["备份与恢复"])

def get_data_paths():
    """获取当前数据目录和数据库路径"""
    import config
    data_dir = config.DATA_DIR
    db_path = Path(config.DB_PATH)
    upload_dir = config.UPLOAD_DIR
    backup_dir = config.BACKUP_DIR
    return data_dir, db_path, upload_dir, backup_dir


@router.get("/create")
async def create_backup(user: User = Depends(require_role("admin"))):
    """导出完整数据备份（数据库 + 照片）为一个 .tar.gz 文件"""
    data_dir, db_path, upload_dir, _ = get_data_paths()

    buf = io.BytesIO()
    with tarfile.open(fileobj=buf, mode="w:gz") as tar:
        backup_info = {
            "magic": BACKUP_MAGIC,
            "version": VERSION,
            "created_at": datetime.now().isoformat(),
            "db_path": db_path.name,
        }
        info_data = json.dumps(backup_info, ensure_ascii=False, indent=2).encode()
        info_tar = tarfile.TarInfo(name="backup.json")
        info_tar.size = len(info_data)
        tar.addfile(info_tar, io.BytesIO(info_data))

        if db_path.exists():
            db_size = db_path.stat().st_size
            db_tar = tarfile.TarInfo(name="vehicle_mgr.db")
            db_tar.size = db_size
            with open(str(db_path), "rb") as f:
                tar.addfile(db_tar, f)
        else:
            raise HTTPException(500, "数据库文件不存在")

        if upload_dir.exists():
            for fpath in sorted(upload_dir.rglob("*")):
                if fpath.is_file():
                    arcname = f"photos/{fpath.relative_to(upload_dir)}"
                    tar.add(str(fpath), arcname=arcname)

    buf.seek(0)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    return StreamingResponse(
        buf,
        media_type="application/gzip",
        headers={"Content-Disposition": f'attachment; filename="vehicle-mgr-backup-{ts}.tar.gz"'},
    )


@router.get("/list")
async def list_backups(user: User = Depends(require_role("admin"))):
    """列出服务器上的自动备份文件"""
    _, _, _, backup_dir = get_data_paths()
    files = []
    if backup_dir.exists():
        for f in sorted(backup_dir.iterdir(), key=lambda f: f.stat().st_mtime, reverse=True):
            if f.is_file() and f.name.endswith(".tar.gz"):
                files.append({
                    "name": f.name,
                    "size": f.stat().st_size,
                    "mtime": datetime.fromtimestamp(f.stat().st_mtime).isoformat(),
                })
    return {"backups": files, "backup_dir": str(backup_dir)}


@router.get("/download/{filename}")
async def download_backup(filename: str, user: User = Depends(require_role("admin"))):
    """下载指定备份文件"""
    _, _, _, backup_dir = get_data_paths()
    fpath = backup_dir / filename
    if not fpath.exists() or not fpath.name.endswith(".tar.gz"):
        raise HTTPException(404, "备份文件不存在")
    return FileResponse(str(fpath), media_type="application/gzip",
                        filename=fpath.name)


@router.post("/delete/{filename}")
async def delete_backup(filename: str, user: User = Depends(require_role("admin"))):
    """删除指定备份文件"""
    _, _, _, backup_dir = get_data_paths()
    fpath = backup_dir / filename
    if not fpath.exists() or not fpath.name.endswith(".tar.gz"):
        raise HTTPException(404, "备份文件不存在")
    fpath.unlink()
    return {"ok": True, "message": f"已删除 {filename}"}


@router.post("/trigger-auto")
async def trigger_auto_backup(user: User = Depends(require_role("admin"))):
    """手动触发一次自动备份"""
    from backup_scheduler import run_full_backup as run_backup, clean_old_backups
    data_dir, db_path, upload_dir, backup_dir = get_data_paths()
    result = await run_backup(data_dir, db_path, upload_dir)
    if result:
        clean_old_backups(backup_dir, 999)  # 不删
        return {"ok": True, "message": f"备份完成: {result.name} ({result.stat().st_size/1024:.0f} KB)"}
    else:
        raise HTTPException(500, "备份失败")


@router.post("/import")
async def import_backup(
    file: UploadFile = File(...),
    user: User = Depends(require_role("admin")),
):
    """导入备份文件，恢复数据"""
    data_dir, db_path, upload_dir, _ = get_data_paths()

    if not file.filename or not file.filename.endswith((".tar.gz", ".tgz")):
        raise HTTPException(400, "请上传 .tar.gz 格式的备份文件")

    try:
        content = await file.read()
        tar_file = tarfile.open(fileobj=io.BytesIO(content), mode="r:gz")
    except Exception:
        raise HTTPException(400, "无法解析备份文件，格式不正确")

    try:
        info_data = tar_file.extractfile("backup.json")
        if info_data is None:
            raise ValueError("缺少 backup.json")
        backup_info = json.loads(info_data.read())
        if backup_info.get("magic") != BACKUP_MAGIC:
            raise ValueError(f"magic 不匹配: {backup_info.get('magic')}")
    except Exception as e:
        raise HTTPException(400, f"无效的备份文件: {e}")

    # 导入前自动备份当前数据
    pre_bak_dir = data_dir / ".pre_restore"
    pre_bak_dir.mkdir(parents=True, exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    pre_bak_file = pre_bak_dir / f"pre_restore_{ts}.tar.gz"
    try:
        with tarfile.open(str(pre_bak_file), "w:gz") as bak:
            if db_path.exists():
                bak.add(str(db_path), arcname=db_path.name)
            if upload_dir.exists():
                bak.add(str(upload_dir), arcname="photos")
    except Exception:
        pass

    # 恢复数据库
    try:
        db_member = tar_file.getmember("vehicle_mgr.db")
        db_tmp = db_path.with_suffix(".db.tmp")
        with open(str(db_tmp), "wb") as f:
            f.write(tar_file.extractfile(db_member).read())
        shutil.move(str(db_tmp), str(db_path))
    except KeyError:
        raise HTTPException(400, "备份文件中缺少 vehicle_mgr.db")

    # 恢复照片
    try:
        photo_members = [m for m in tar_file.getmembers() if m.name.startswith("photos/")]
        if photo_members:
            old_photos_bak = data_dir / ".old_photos"
            if upload_dir.exists() and any(upload_dir.iterdir()):
                if old_photos_bak.exists():
                    shutil.rmtree(str(old_photos_bak))
                shutil.move(str(upload_dir), str(old_photos_bak))
            upload_dir.mkdir(parents=True, exist_ok=True)
            for m in photo_members:
                if m.isfile():
                    rel = Path(m.name).relative_to("photos")
                    target = upload_dir / rel
                    target.parent.mkdir(parents=True, exist_ok=True)
                    with open(str(target), "wb") as f:
                        f.write(tar_file.extractfile(m).read())
    except Exception as e:
        print(f"[backup] 照片恢复失败: {e}")

    tar_file.close()
    return {"ok": True, "message": "数据已恢复，建议重启服务以刷新连接"}
