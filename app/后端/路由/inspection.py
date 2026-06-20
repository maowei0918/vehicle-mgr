"""日检管理"""
import json
import logging
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from fastapi.responses import Response
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc, func
from pydantic import BaseModel
from database import get_db
from models.inspection import Inspection
from models.vehicle import Vehicle
from models.user import User
from services.auth import get_current_user, require_role
from services.operation_log import log_operation
from services.permissions import scope_query
from services.ocr import recognize_mileage
from config import UPLOAD_DIR, MILEAGE_THRESHOLD

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/inspections", tags=["日检"])


@router.post("/upload")
async def upload_photo(file: UploadFile = File(...), user: User = Depends(get_current_user)):
    """上传日检照片"""
    import uuid
    ext = file.filename.split(".")[-1] if "." in file.filename else "jpg"
    fname = f"{uuid.uuid4().hex}.{ext}"
    path = UPLOAD_DIR / fname
    content = await file.read()
    path.write_bytes(content)
    return {"url": f"/uploads/{fname}"}


@router.post("")
async def create_inspection(
    vehicle_id: int = Form(...),
    exterior_photos: str = Form("[]"),
    cabin_photos: str = Form("[]"),
    odometer_photo: str = Form(""),
    issues: str = Form(""),
    manual_odometer: int = Form(0),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_role("driver", "fleet_manager", "admin")),
):
    """提交日检"""
    # 验证车辆
    vehicle = await db.get(Vehicle, vehicle_id)
    if not vehicle:
        raise HTTPException(404, "车辆不存在")

    # 查询上次里程
    last_result = await db.execute(
        select(Inspection).where(Inspection.vehicle_id == vehicle_id)
        .order_by(desc(Inspection.id)).limit(1)
    )
    last = last_result.scalar_one_or_none()
    last_odo = last.odometer_reading if last else None

    # OCR 识别里程数
    odometer_reading = manual_odometer if manual_odometer > 0 else None
    if odometer_photo and odometer_reading is None:
        photo_path = UPLOAD_DIR / odometer_photo.split("/")[-1]
        if photo_path.exists():
            ai_result = await recognize_mileage(photo_path)
            if ai_result:
                odometer_reading = ai_result

    # 计算差值
    mileage_diff = None
    threshold_exceeded = False
    if odometer_reading and last_odo:
        mileage_diff = odometer_reading - last_odo
        if mileage_diff > MILEAGE_THRESHOLD:
            threshold_exceeded = True

    insp = Inspection(
        vehicle_id=vehicle_id,
        driver_id=user.id,
        inspection_date="",
        exterior_photos=exterior_photos,
        cabin_photos=cabin_photos,
        odometer_photo=odometer_photo,
        odometer_reading=odometer_reading,
        last_odometer=last_odo,
        mileage_diff=mileage_diff,
        threshold_exceeded=threshold_exceeded,
        issues=issues,
    )
    from datetime import date
    insp.inspection_date = date.today().isoformat()

    db.add(insp)
    await db.commit()
    await db.refresh(insp)
    plate = vehicle.plate_number if vehicle else ""
    await log_operation(db, user, f"提交了「{plate}」的日检", "inspection", insp.id)

    return {
        "id": insp.id,
        "odometer_reading": odometer_reading,
        "last_odometer": last_odo,
        "mileage_diff": mileage_diff,
        "threshold_exceeded": threshold_exceeded,
    }


@router.get("")
async def list_inspections(
    vehicle_id: int | None = None,
    page: int = 1,
    size: int = 20,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """日检列表"""
    query = select(Inspection).order_by(desc(Inspection.id))
    count_query = select(func.count(Inspection.id)).select_from(Inspection)
    if vehicle_id:
        query = query.where(Inspection.vehicle_id == vehicle_id)
        count_query = count_query.where(Inspection.vehicle_id == vehicle_id)
    query = await scope_query(query, user, Inspection)
    count_query = await scope_query(count_query, user, Inspection)

    total_r = await db.execute(count_query)
    total = total_r.scalar() or 0
    query = query.offset((page - 1) * size).limit(size)
    result = await db.execute(query)
    items = result.scalars().all()

    return {"items": [{
        "id": i.id, "vehicle_id": i.vehicle_id, "driver_id": i.driver_id,
        "inspection_date": i.inspection_date,
        "odometer_reading": i.odometer_reading,
        "last_odometer": i.last_odometer,
        "mileage_diff": i.mileage_diff,
        "threshold_exceeded": bool(i.threshold_exceeded) if i.threshold_exceeded is not None else False,
        "issues": i.issues,
        "status": i.status,
    } for i in items],
        "total": total,
        "page": page,
        "size": size
    }


@router.get("/check-mileage/{vehicle_id}")
async def check_mileage(vehicle_id: int, db: AsyncSession = Depends(get_db),
                        user: User = Depends(get_current_user)):
    """检查最近两次里程差值，返回是否超阈值"""
    result = await db.execute(
        select(Inspection).where(Inspection.vehicle_id == vehicle_id, Inspection.odometer_reading.isnot(None))
        .order_by(desc(Inspection.id)).limit(2)
    )
    records = result.scalars().all()
    if len(records) < 2:
        return {"exceeded": False, "diff": None, "message": "数据不足"}
    diff = records[0].odometer_reading - records[1].odometer_reading
    return {
        "exceeded": diff > MILEAGE_THRESHOLD,
        "diff": diff,
        "current": records[0].odometer_reading,
        "previous": records[1].odometer_reading,
        "threshold": MILEAGE_THRESHOLD,
    }


@router.get("/export")
async def export_inspections(
    start_date: str | None = None,
    end_date: str | None = None,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """导出日检 CSV"""
    query = select(Inspection).order_by(desc(Inspection.id))
    query = await scope_query(query, user, Inspection)

    result = await db.execute(query)
    items = result.scalars().all()

    import csv, io
    buf = io.StringIO()
    w = csv.writer(buf)
    w.writerow(["日期", "车牌号", "驾驶员", "里程数", "上次里程", "里程差", "超阈值", "问题"])
    for i in items:
        vehicle = await db.get(Vehicle, i.vehicle_id)
        plate = vehicle.plate_number if vehicle else ""
        driver_name = vehicle.driver.name if vehicle and vehicle.driver else ""
        w.writerow([
            i.inspection_date or "", plate, driver_name,
            i.odometer_reading or "", i.last_odometer or "", i.mileage_diff or "",
            "是" if i.threshold_exceeded else "否", i.issues or ""
        ])
    return Response(content=buf.getvalue(), media_type="text/csv; charset=utf-8",
                    headers={"Content-Disposition": "attachment; filename=inspections.csv"})
