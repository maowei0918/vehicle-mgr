"""自动定期备份调度器"""
import asyncio, json, os, shutil, tarfile, logging
from datetime import datetime
from pathlib import Path
from io import BytesIO

logger = logging.getLogger("backup_scheduler")

# 默认配置
DEFAULT_INTERVAL_HOURS = 24
DEFAULT_RETENTION = 7

# 全局调度任务引用
_scheduler_task = None


async def run_backup(data_dir: Path, db_path: Path, upload_dir: Path) -> Path | None:
    """执行一次备份，保存到 data/backups/ 目录，返回备份文件路径"""
    backup_dir = data_dir / "backups"
    backup_dir.mkdir(parents=True, exist_ok=True)

    ts = datetime.now().strftime("%Y%m%d-%H%M%S")
    out_path = backup_dir / f"auto-backup-{ts}.tar.gz"

    try:
        with tarfile.open(str(out_path), "w:gz") as tar:
            # backup.json 元信息
            info = {
                "magic": "vehicle-mgr-backup-v1",
                "type": "auto",
                "created_at": datetime.now().isoformat(),
                "db_path": db_path.name,
            }
            info_data = json.dumps(info, ensure_ascii=False, indent=2).encode()
            info_tar = tarfile.TarInfo(name="backup.json")
            info_tar.size = len(info_data)
            tar.addfile(info_tar, BytesIO(info_data))

            # 数据库
            if db_path.exists():
                db_size = db_path.stat().st_size
                db_tar = tarfile.TarInfo(name="vehicle_mgr.db")
                db_tar.size = db_size
                with open(str(db_path), "rb") as f:
                    tar.addfile(db_tar, f)
            else:
                logger.warning("数据库文件不存在，跳过")

            # 照片
            if upload_dir.exists():
                for fpath in sorted(upload_dir.rglob("*")):
                    if fpath.is_file():
                        arcname = f"photos/{fpath.relative_to(upload_dir)}"
                        tar.add(str(fpath), arcname=arcname)

        logger.info(f"自动备份完成: {out_path.name} ({out_path.stat().st_size / 1024 / 1024:.1f} MB)")
        return out_path
    except Exception as e:
        logger.error(f"自动备份失败: {e}")
        return None


def clean_old_backups(backup_dir: Path, retention: int):
    """删除旧备份，只保留最近 retention 个"""
    if not backup_dir.exists():
        return
    backups = sorted(
        [f for f in backup_dir.iterdir() if f.name.startswith("auto-backup-") and f.name.endswith(".tar.gz")],
        key=lambda f: f.stat().st_mtime,
        reverse=True,
    )
    if len(backups) > retention:
        for old in backups[retention:]:
            try:
                old.unlink()
                logger.info(f"删除旧备份: {old.name}")
            except Exception as e:
                logger.error(f"删除旧备份失败 {old.name}: {e}")


async def scheduler_loop(data_dir: Path, db_path: Path, upload_dir: Path, get_settings_func):
    """定时备份循环"""
    while True:
        try:
            # 从设置中读取配置
            settings = get_settings_func()
            interval_hours = float(settings.get("BACKUP_INTERVAL_HOURS", DEFAULT_INTERVAL_HOURS))
            retention = int(settings.get("BACKUP_RETENTION", DEFAULT_RETENTION))
        except Exception:
            interval_hours = DEFAULT_INTERVAL_HOURS
            retention = DEFAULT_RETENTION

        if interval_hours > 0:
            backup_dir = data_dir / "backups"
            await run_backup(data_dir, db_path, upload_dir)
            clean_old_backups(backup_dir, retention)

        # 等待到下一个周期
        await asyncio.sleep(interval_hours * 3600)


def start_scheduler(data_dir: Path, db_path: Path, upload_dir: Path, get_settings_func):
    """启动定时备份调度器（在 app startup 时调用）"""
    global _scheduler_task
    if _scheduler_task is not None:
        return  # 已启动

    async def _run():
        # 首次启动等 60 秒再执行，避免刚启动时过于频繁
        await asyncio.sleep(60)
        await scheduler_loop(data_dir, db_path, upload_dir, get_settings_func)

    _scheduler_task = asyncio.create_task(_run())
    logger.info("自动备份调度器已启动")


def stop_scheduler():
    """停止调度器"""
    global _scheduler_task
    if _scheduler_task:
        _scheduler_task.cancel()
        _scheduler_task = None
        logger.info("自动备份调度器已停止")
