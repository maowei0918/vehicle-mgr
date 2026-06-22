"""全量 + 定期增量备份调度器"""
import asyncio, json, os, shutil, tarfile, logging
from datetime import datetime, timedelta
from pathlib import Path
from io import BytesIO

logger = logging.getLogger("backup_scheduler")

# ── 全量备份 ─────────────────────────────────────────────


async def run_full_backup(data_dir: Path, db_path: Path, upload_dir: Path) -> Path | None:
    """执行一次全量数据库+照片备份，保存到 data/backups/ 目录"""
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

            if db_path.exists():
                db_size = db_path.stat().st_size
                db_tar = tarfile.TarInfo(name="vehicle_mgr.db")
                db_tar.size = db_size
                with open(str(db_path), "rb") as f:
                    tar.addfile(db_tar, f)

            if upload_dir.exists():
                for fpath in sorted(upload_dir.rglob("*")):
                    if fpath.is_file():
                        arcname = f"photos/{fpath.relative_to(upload_dir)}"
                        tar.add(str(fpath), arcname=arcname)

        logger.info(f"全量备份完成: {out_path.name} ({out_path.stat().st_size / 1024 / 1024:.1f} MB)")
        return out_path
    except Exception as e:
        logger.error(f"全量备份失败: {e}")
        return None


def clean_old_backups(backup_dir: Path, retention: int):
    """删除旧全量备份，只保留最近 retention 个"""
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
                logger.info(f"删除旧全量备份: {old.name}")
            except Exception as e:
                logger.error(f"删除旧全量备份失败 {old.name}: {e}")


# ── 定期增量备份 ──────────────────────────────────────────
# 运行时动态导入以避免循环引用


async def run_regular_backup(data_dir: Path, days: int = 30) -> Path | None:
    """执行一次定期增量备份（按天数范围导出数据）"""
    try:
        from routers.regular_backup import REGULAR_MAGIC, VERSION, TABLE_CONF, _obj_to_dict
        from models.user import User, Group
        from models.vehicle import Vehicle
        from models.inspection import Inspection
        from models.repair import Repair
        from models.repair_flow import RepairFlow
        from models.contract import Contract
        from models.contract_part import ContractPart
        from models.role import Role, RolePermission
        from models.operation_log import OperationLog
        from sqlalchemy.ext.asyncio import AsyncSession
        from sqlalchemy import select
        from database import get_db, SessionLocal
        from config import REGULAR_BACKUP_ENABLED, REGULAR_BACKUP_INTERVAL_HOURS, REGULAR_BACKUP_DAYS

        backup_dir = data_dir / "backups"
        backup_dir.mkdir(parents=True, exist_ok=True)

        # 创建自己的异步 session
        from database import SessionLocal
        from contextlib import asynccontextmanager

        async with SessionLocal() as db:
            end = datetime.now()
            start = end - timedelta(days=days)

            payload = {
                "magic": REGULAR_MAGIC, "version": VERSION,
                "start": start.isoformat(), "end": end.isoformat(),
                "data": {},
            }

            for name, model, date_col, is_ref in TABLE_CONF:
                if is_ref:
                    rows = (await db.execute(select(model))).scalars().all()
                else:
                    col = getattr(model, date_col)
                    stmt = select(model).where(col >= start, col <= end)
                    rows = (await db.execute(stmt)).scalars().all()
                payload["data"][name] = [_obj_to_dict(r) for r in rows]
                logger.info(f"  增量({name}): {len(rows)} 条")

            raw = json.dumps(payload, ensure_ascii=False, indent=2).encode()
            ts = end.strftime("%Y%m%d")
            start_str = start.strftime("%Y%m%d")
            fname = f"regular-{start_str}-{ts}.tar.gz"
            out_path = backup_dir / fname

            with tarfile.open(str(out_path), "w:gz") as tar:
                info = tarfile.TarInfo(name="regular_data.json")
                info.size = len(raw)
                tar.addfile(info, BytesIO(raw))

        size_mb = out_path.stat().st_size / 1024 / 1024
        logger.info(f"增量备份完成: {fname} ({size_mb:.1f} MB)")
        return out_path
    except Exception as e:
        logger.error(f"增量备份失败: {e}")
        return None


def clean_regular_backups(backup_dir: Path, retention: int = 30):
    """删除旧增量备份，只保留最近 retention 个"""
    if not backup_dir.exists():
        return
    backups = sorted(
        [f for f in backup_dir.iterdir() if f.name.startswith("regular-") and f.name.endswith(".tar.gz")],
        key=lambda f: f.stat().st_mtime,
        reverse=True,
    )
    if len(backups) > retention:
        for old in backups[retention:]:
            try:
                old.unlink()
                logger.info(f"删除旧增量备份: {old.name}")
            except Exception as e:
                logger.error(f"删除旧增量备份失败 {old.name}: {e}")


# ── 调度循环 ──────────────────────────────────────────────

async def scheduler_loop(data_dir: Path, db_path: Path, upload_dir: Path, get_settings_func):
    """定时备份主循环（全量 + 增量）"""
    from config import REGULAR_BACKUP_ENABLED, REGULAR_BACKUP_INTERVAL_HOURS, REGULAR_BACKUP_DAYS

    while True:
        try:
            settings = get_settings_func() if callable(get_settings_func) else {}
            full_hours = int(settings.get("BACKUP_INTERVAL_HOURS", 24))
            full_ret = int(settings.get("BACKUP_RETENTION", 7))
            reg_on = settings.get("REGULAR_BACKUP_ENABLED", str(REGULAR_BACKUP_ENABLED)).lower() == "true"
            reg_hours = int(settings.get("REGULAR_BACKUP_INTERVAL_HOURS", REGULAR_BACKUP_INTERVAL_HOURS))
            reg_days = int(settings.get("REGULAR_BACKUP_DAYS", REGULAR_BACKUP_DAYS))

            backup_dir = data_dir / "backups"
            backup_dir.mkdir(parents=True, exist_ok=True)

            # ── 全量备份（每小时第 3 分钟执行） ──
            if datetime.now().minute < 5:
                await run_full_backup(data_dir, db_path, upload_dir)
                clean_old_backups(backup_dir, full_ret)
                await asyncio.sleep(300)

            # ── 增量备份（每 reg_hours 小时的第 15 分钟执行） ──
            if reg_on and datetime.now().minute >= 14 and datetime.now().minute < 16:
                await run_regular_backup(data_dir, reg_days)
                clean_regular_backups(backup_dir, 30)
                await asyncio.sleep(120)

            # 等待一分钟再检查
            await asyncio.sleep(60)
        except asyncio.CancelledError:
            break
        except Exception as e:
            logger.error(f"调度器循环异常: {e}")
            await asyncio.sleep(120)


_scheduler_task = None


def start_scheduler(data_dir: Path, db_path: Path, upload_dir: Path, get_settings_func=None):
    """在 lifespan 中调用，启动后台调度任务"""
    global _scheduler_task
    if _scheduler_task is not None and not _scheduler_task.done():
        _scheduler_task.cancel()

    async def _run():
        await scheduler_loop(data_dir, db_path, upload_dir, get_settings_func)

    loop = asyncio.get_event_loop()
    _scheduler_task = loop.create_task(_run())
