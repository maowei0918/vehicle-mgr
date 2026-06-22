"""数据备份与恢复"""
import io, json, os, shutil, tarfile, hashlib
from datetime import datetime
from pathlib import Path
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from database import get_db, engine, DATABASE_URL
from models.user import User
from services.auth import get_current_user, require_role

VERSION = "14.0.0"
BACKUP_MAGIC = "vehicle-mgr-backup-v1"

router = APIRouter(prefix="/api/backup", tags=["备份与恢复"])

def get_data_paths():
    """获取当前数据目录和数据库路径"""
    import config
    data_dir = config.DATA_DIR
    db_path = Path(config.DB_PATH)
    upload_dir = config.UPLOAD_DIR
    return data_dir, db_path, upload_dir


@router.get("/create")
async def create_backup(user: User = Depends(require_role("admin"))):
    """导出完整数据备份（数据库 + 照片）为一个 .tar.gz 文件"""
    data_dir, db_path, upload_dir = get_data_paths()

    buf = io.BytesIO()
    with tarfile.open(fileobj=buf, mode="w:gz") as tar:
        # 1. 备份元信息
        backup_info = {
            "magic": BACKUP_MAGIC,
            "version": VERSION,
            "created_at": datetime.now().isoformat(),
            "db_path": db_path.name,
        }
        info_data = json.dumps(backup_info, ensure_ascii=False, indent=2).encode()
        info_buf = io.BytesIO(info_data)
        info_tar = tarfile.TarInfo(name="backup.json")
        info_tar.size = len(info_data)
        tar.addfile(info_tar, info_buf)

        # 2. 数据库文件
        if db_path.exists():
            db_size = db_path.stat().st_size
            db_tar = tarfile.TarInfo(name="vehicle_mgr.db")
            db_tar.size = db_size
            with open(str(db_path), "rb") as f:
                tar.addfile(db_tar, f)
        else:
            raise HTTPException(500, "数据库文件不存在")

        # 3. 照片目录
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


@router.post("/import")
async def import_backup(
    file: UploadFile = File(...),
    user: User = Depends(require_role("admin")),
):
    """导入备份文件，恢复数据"""
    data_dir, db_path, upload_dir = get_data_paths()

    if not file.filename or not file.filename.endswith((".tar.gz", ".tgz")):
        raise HTTPException(400, "请上传 .tar.gz 格式的备份文件")

    # 读取上传的 tar.gz
    try:
        content = await file.read()
        tar_file = tarfile.open(fileobj=io.BytesIO(content), mode="r:gz")
    except Exception:
        raise HTTPException(400, "无法解析备份文件，格式不正确")

    # 验证 backup.json
    try:
        info_data = tar_file.extractfile("backup.json")
        if info_data is None:
            raise ValueError("缺少 backup.json")
        backup_info = json.loads(info_data.read())
        if backup_info.get("magic") != BACKUP_MAGIC:
            raise ValueError(f"magic 不匹配: {backup_info.get('magic')}")
    except Exception as e:
        raise HTTPException(400, f"无效的备份文件: {e}")

    # 在恢复前自动备份当前数据
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
        pass  # 预备份失败不阻塞导入
    print(f"[backup] 导入前自动备份: {pre_bak_file}")

    # 恢复数据库文件
    try:
        db_member = tar_file.getmember("vehicle_mgr.db")
        db_tmp = db_path.with_suffix(".db.tmp")
        with open(str(db_tmp), "wb") as f:
            f.write(tar_file.extractfile(db_member).read())
        shutil.move(str(db_tmp), str(db_path))
        print(f"[backup] 数据库已恢复: {db_path}")
    except KeyError:
        raise HTTPException(400, "备份文件中缺少 vehicle_mgr.db")

    # 恢复照片目录
    try:
        photo_members = [m for m in tar_file.getmembers() if m.name.startswith("photos/")]
        if photo_members:
            # 备份旧照片
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
            print(f"[backup] 已恢复 {len(photo_members)} 个文件到 {upload_dir}")
    except Exception as e:
        print(f"[backup] 照片恢复失败: {e}")

    tar_file.close()

    return {"ok": True, "message": "数据已恢复，建议重启服务以刷新连接"}
