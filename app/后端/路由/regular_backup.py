"""定期增量备份 — 按时间范围导出/导入业务数据"""
import io, json, tarfile, logging
from datetime import datetime, date, timedelta
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, DateTime, Date, Text, String
from database import get_db
from models.user import User, Group
from models.vehicle import Vehicle
from models.inspection import Inspection
from models.repair import RepairOrder, RepairDetail, WarrantyAlert
from models.repair_flow import RepairFlow
from models.contract import Contract
from models.contract_part import ContractPart
from models.role import Role, RolePermission
from models.operation_log import OperationLog
from services.auth import get_current_user, require_role

logger = logging.getLogger("regular_backup")
REGULAR_MAGIC = "vehicle-mgr-regular-v1"
VERSION = "14.0.0"

# ── 表配置 ──────────────────────────────────────────────
# (model_class, date_field, 是否参考表)
TABLE_CONF = [
    # 参考数据（先导入，全量导出）
    ("roles",          Role,          "created_at", True),
    ("role_permissions", RolePermission, "created_at", True),
    ("groups",         Group,         "created_at", True),
    ("users",          User,          "created_at", True),
    # 业务数据（按时间范围导出）
    ("inspections",    Inspection,    "created_at", False),
    ("repairs",        RepairOrder,   "created_at", False),
    ("repair_details", RepairDetail,  "created_at", False),
    ("warranty_alerts", WarrantyAlert, "created_at", False),
    ("repair_flows",   RepairFlow,    "created_at", False),
    ("contracts",      Contract,      "created_at", False),
    ("contract_parts", ContractPart,  "created_at", False),
    ("vehicles",       Vehicle,       "created_at", False),
    ("operation_logs", OperationLog,  "created_at", False),
]

router = APIRouter(prefix="/api/backup/regular", tags=["定期增量备份"])


def _obj_to_dict(obj):
    """ORM → dict，datetime/date 转 iso 字符串"""
    d = {}
    for col in obj.__table__.columns:
        val = getattr(obj, col.name)
        if val is None:
            d[col.name] = None
        elif isinstance(val, (datetime, date)):
            d[col.name] = val.isoformat()
        elif isinstance(val, timedelta):
            d[col.name] = str(val)
        else:
            d[col.name] = val
    return d


def _cast_from_iso(obj_cls, data: dict) -> dict:
    """把 dict 中 iso 字符串转回 datetime/date，适配自动 commit"""
    out = {}
    for col in obj_cls.__table__.columns:
        key = col.name
        if key not in data:
            continue
        val = data[key]
        if val is None:
            out[key] = None
        elif isinstance(col.type, DateTime):
            if isinstance(val, str):
                out[key] = datetime.fromisoformat(val)
            else:
                out[key] = val
        elif isinstance(col.type, Date):
            if isinstance(val, str):
                out[key] = date.fromisoformat(val)
            else:
                out[key] = val
        else:
            out[key] = val
    return out


@router.post("/create")
async def create_regular_backup(
    days: int = Query(30, ge=1, le=3650, description="备份近期多少天的数据"),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_role("admin")),
):
    """按时间范围导出业务数据为 regular-<开始日期>-<结束日期>.tar.gz"""
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
        logger.info(f"  {name}: {len(rows)} 条")

    raw = json.dumps(payload, ensure_ascii=False, indent=2).encode()
    buf = io.BytesIO()
    with tarfile.open(fileobj=buf, mode="w:gz") as tar:
        info = tarfile.TarInfo(name="regular_data.json")
        info.size = len(raw)
        tar.addfile(info, io.BytesIO(raw))

    buf.seek(0)
    fname = f"regular-{start.strftime('%Y%m%d')}-{end.strftime('%Y%m%d')}.tar.gz"
    return StreamingResponse(
        buf, media_type="application/gzip",
        headers={"Content-Disposition": f'attachment; filename="{fname}"'},
    )


@router.post("/import")
async def import_regular_backup(
    file: UploadFile = File(...),
    conflict: str = Query("newer", regex="^(newer|skip|overwrite)$"),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_role("admin")),
):
    """导入定期备份，合并数据。

    conflict 策略:
      - newer   : 按 created_at 比较，取新的
      - skip    : 已有记录不覆盖
      - overwrite: 全部覆盖
    """
    if not file.filename or not file.filename.endswith(".tar.gz"):
        raise HTTPException(400, "请上传 .tar.gz 格式文件")

    raw = await file.read()
    try:
        tar = tarfile.open(fileobj=io.BytesIO(raw), mode="r:gz")
        fp = tar.extractfile("regular_data.json")
        if not fp:
            raise ValueError("缺少 regular_data.json")
        payload = json.loads(fp.read())
    except Exception as e:
        raise HTTPException(400, f"无法解析备份文件: {e}")

    if payload.get("magic") != REGULAR_MAGIC:
        raise HTTPException(400, "不是有效的定期备份文件")

    data = payload.get("data", {})
    stats = {"insert": 0, "update": 0, "skip": 0, "error": 0}
    order = [name for name, _, _, _ in TABLE_CONF]  # 保证导入顺序

    for name in order:
        rows = data.get(name, [])
        # 找到模型配置
        _, model, date_col, is_ref = next(
            (a, b, c, d) for a, b, c, d in TABLE_CONF if a == name
        )

        for row in rows:
            try:
                pk = row.get("id")
                if pk is None:
                    continue
                exist = await db.get(model, pk)
                if exist is None:
                    # ── 插入新记录 ──
                    vals = _cast_from_iso(model, row)
                    obj = model(**vals)
                    db.add(obj)
                    stats["insert"] += 1
                else:
                    # ── 已存在 → 按策略处理 ──
                    if conflict == "skip":
                        stats["skip"] += 1
                        continue

                    imp_date_str = row.get(date_col)
                    imp_dt = None
                    if imp_date_str:
                        try:
                            imp_dt = datetime.fromisoformat(imp_date_str)
                        except Exception:
                            pass

                    cur_dt = getattr(exist, date_col, None)
                    if isinstance(cur_dt, date) and not isinstance(cur_dt, datetime):
                        cur_dt = datetime.combine(cur_dt, datetime.min.time())

                    should_upd = conflict == "overwrite"
                    if conflict == "newer" and imp_dt and cur_dt:
                        should_upd = imp_dt > cur_dt

                    if should_upd:
                        vals = _cast_from_iso(model, row)
                        for k, v in vals.items():
                            if k != "id":
                                setattr(exist, k, v)
                        await db.flush()
                        stats["update"] += 1
                    else:
                        stats["skip"] += 1

            except Exception as e:
                stats["error"] += 1
                logger.warning(f"导入 {name}#{row.get('id')} 失败: {e}")

    await db.commit()
    return {
        "ok": True,
        "message": f"新 {stats['insert']} / 更新 {stats['update']} / 跳过 {stats['skip']} / 错误 {stats['error']}",
    }
