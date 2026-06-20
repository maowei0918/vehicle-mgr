from pathlib import Path
base = Path('/vol1/@appcenter/vehicle-mgr/后端')

(base/'路由/vehicle.py').write_text(r'''"""车辆管理"""
import openpyxl
from io import BytesIO
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel
from database import get_db
from 模型.vehicle import Vehicle
from 模型.user import User
from 服务.auth import get_current_user, require_role
from 服务.permissions import is_manager, ensure_group_user, scoped_vehicle_query, ensure_vehicle_access

router = APIRouter(prefix="/api/vehicles", tags=["车辆"])

class VehicleReq(BaseModel):
    plate_number: str
    brand: str = ""
    model: str = ""
    color: str = ""
    vin: str = ""
    group_id: int | None = None
    driver_id: int | None = None
    notes: str = ""


def vehicle_dict(v: Vehicle):
    return {"id": v.id, "plate_number": v.plate_number, "brand": v.brand, "model": v.model, "color": v.color, "vin": v.vin, "group_id": v.group_id, "group_name": v.group.name if v.group else "", "driver_id": v.driver_id, "driver_name": v.driver.name if v.driver else "", "status": "active" if v.is_active else "retired", "is_active": v.is_active, "notes": v.notes}

async def validate_vehicle_assignment(db: AsyncSession, req: VehicleReq, user: User):
    if is_manager(user):
        ensure_group_user(user)
        req.group_id = user.group_id
    if req.driver_id:
        d = await db.get(User, req.driver_id)
        if not d or d.role != "driver":
            raise HTTPException(400, "请选择驾驶员")
        if req.group_id and d.group_id != req.group_id:
            raise HTTPException(400, "驾驶员不属于该分组")

@router.get("")
async def list_vehicles(q: str | None = None, db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    query = select(Vehicle).order_by(Vehicle.id)
    query = await scoped_vehicle_query(query, user)
    if q:
        query = query.where(Vehicle.plate_number.like(f"%{q}%"))
    result = await db.execute(query)
    return [vehicle_dict(v) for v in result.scalars().all()]

@router.get("/{vid}")
async def get_vehicle(vid: str, db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    if vid.isdigit():
        v = await db.get(Vehicle, int(vid))
    else:
        rs = await db.execute(select(Vehicle).where(Vehicle.plate_number == vid))
        v = rs.scalar_one_or_none()
    await ensure_vehicle_access(db, user, v)
    return vehicle_dict(v)

@router.post("")
async def create_vehicle(req: VehicleReq, db: AsyncSession = Depends(get_db), user: User = Depends(require_role("admin", "fleet_manager", "manager", "dispatcher"))):
    if not req.plate_number:
        raise HTTPException(400, "车牌号不能为空")
    exist = await db.execute(select(Vehicle).where(Vehicle.plate_number == req.plate_number))
    if exist.first():
        raise HTTPException(400, "车牌号已存在")
    await validate_vehicle_assignment(db, req, user)
    v = Vehicle(**req.model_dump())
    db.add(v)
    await db.commit()
    await db.refresh(v)
    return vehicle_dict(v)

@router.put("/{vid}")
async def update_vehicle(vid: str, req: VehicleReq, db: AsyncSession = Depends(get_db), user: User = Depends(require_role("admin", "fleet_manager", "manager", "dispatcher"))):
    if vid.isdigit():
        v = await db.get(Vehicle, int(vid))
    else:
        rs = await db.execute(select(Vehicle).where(Vehicle.plate_number == vid))
        v = rs.scalar_one_or_none()
    await ensure_vehicle_access(db, user, v)
    await validate_vehicle_assignment(db, req, user)
    for key, val in req.model_dump().items():
        setattr(v, key, val)
    await db.commit()
    return {"msg": "已更新"}

@router.delete("/{vid}")
async def delete_vehicle(vid: str, db: AsyncSession = Depends(get_db), user: User = Depends(require_role("admin", "fleet_manager", "manager", "dispatcher"))):
    if vid.isdigit():
        v = await db.get(Vehicle, int(vid))
    else:
        rs = await db.execute(select(Vehicle).where(Vehicle.plate_number == vid))
        v = rs.scalar_one_or_none()
    await ensure_vehicle_access(db, user, v)
    await db.delete(v)
    await db.commit()
    return {"msg": "已删除"}

@router.post("/import")
async def import_vehicles(items: list[VehicleReq], db: AsyncSession = Depends(get_db), user: User = Depends(require_role("admin", "fleet_manager", "manager", "dispatcher"))):
    imported = skipped = 0
    errors = []
    for idx, req in enumerate(items, start=1):
        try:
            if not req.plate_number:
                skipped += 1; continue
            exist = await db.execute(select(Vehicle).where(Vehicle.plate_number == req.plate_number))
            if exist.first():
                skipped += 1; continue
            await validate_vehicle_assignment(db, req, user)
            db.add(Vehicle(**req.model_dump()))
            imported += 1
        except Exception as e:
            skipped += 1; errors.append(f"第{idx}行: {getattr(e, 'detail', str(e))}")
    await db.commit()
    return {"imported": imported, "skipped": skipped, "errors": errors}

@router.post("/import/xlsx")
async def import_vehicles_xlsx(file: UploadFile = File(...), db: AsyncSession = Depends(get_db), user: User = Depends(require_role("admin", "fleet_manager", "manager", "dispatcher"))):
    if not file.filename.endswith((".xlsx", ".xls")):
        raise HTTPException(400, "请上传 .xlsx/.xls 文件")
    wb = openpyxl.load_workbook(BytesIO(await file.read()))
    ws = wb.active
    items=[]
    for row in ws.iter_rows(min_row=2, values_only=True):
        if not row or not row[0]:
            continue
        items.append(VehicleReq(plate_number=str(row[0]).strip(), brand=str(row[1] or "").strip(), model=str(row[2] or "").strip(), color=str(row[3] or "").strip(), vin=str(row[4] or "").strip(), group_id=int(row[5]) if len(row)>5 and row[5] else None, driver_id=int(row[6]) if len(row)>6 and row[6] else None))
    return await import_vehicles(items, db, user)
''', encoding='utf-8')

print('vehicle patched')
