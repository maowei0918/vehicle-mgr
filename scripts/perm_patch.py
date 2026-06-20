from pathlib import Path

base = Path('/vol1/@appcenter/vehicle-mgr/后端')

(base/'服务/permissions.py').write_text(r'''"""权限与数据范围工具"""
from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from 模型.user import User
from 模型.vehicle import Vehicle
from 模型.repair import RepairOrder
from 模型.inspection import Inspection

MANAGER_ROLES = {"fleet_manager", "manager", "dispatcher"}
VALID_ROLES = {"admin", "fleet_manager", "manager", "dispatcher", "repair_shop", "driver"}


def norm_role(role: str) -> str:
    if role in ("manager", "dispatcher"):
        return "fleet_manager"
    return role


def role_name(role: str) -> str:
    return {
        "admin": "管理员",
        "fleet_manager": "车管员",
        "manager": "车管员",
        "dispatcher": "车管员",
        "driver": "驾驶员",
        "repair_shop": "修理厂",
    }.get(role, role)


def is_admin(user: User) -> bool:
    return user.role == "admin"


def is_manager(user: User) -> bool:
    return user.role in MANAGER_ROLES


def ensure_role(user: User, *roles: str):
    allowed = set(roles)
    if "fleet_manager" in allowed:
        allowed |= MANAGER_ROLES
    if user.role not in allowed:
        raise HTTPException(403, "无权限")


def ensure_group_user(user: User):
    if is_manager(user) and not user.group_id:
        raise HTTPException(403, "当前车管员未绑定分组")


def check_username(username: str):
    import re
    if not re.fullmatch(r"[A-Za-z]+", username or ""):
        raise HTTPException(400, "用户名只能使用纯英文字母")


def check_password(password: str, required: bool = False):
    if required and not password:
        raise HTTPException(400, "密码不能为空")
    if password and len(password) < 6:
        raise HTTPException(400, "密码至少 6 位")


def check_phone(phone: str):
    import re
    if phone and not re.fullmatch(r"1\d{10}", phone):
        raise HTTPException(400, "手机号必须为 11 位大陆手机号")


async def scoped_user_query(query, current: User):
    if current.role == "admin":
        return query
    if is_manager(current):
        ensure_group_user(current)
        return query.where(User.group_id == current.group_id)
    return query.where(User.id == current.id)


async def scoped_vehicle_query(query, current: User):
    if current.role == "admin":
        return query
    if is_manager(current):
        ensure_group_user(current)
        return query.where(Vehicle.group_id == current.group_id)
    if current.role == "driver":
        return query.where(Vehicle.driver_id == current.id)
    raise HTTPException(403, "无权访问车辆")


async def ensure_vehicle_access(db: AsyncSession, current: User, vehicle: Vehicle):
    if not vehicle:
        raise HTTPException(404, "车辆不存在")
    if current.role == "admin":
        return
    if is_manager(current):
        ensure_group_user(current)
        if vehicle.group_id == current.group_id:
            return
    if current.role == "driver" and vehicle.driver_id == current.id:
        return
    raise HTTPException(403, "无权访问该车辆")


async def scoped_repair_query(query, current: User, db: AsyncSession):
    if current.role == "admin":
        return query
    if is_manager(current):
        ensure_group_user(current)
        rs = await db.execute(select(Vehicle.id).where(Vehicle.group_id == current.group_id))
        ids = [r[0] for r in rs]
        return query.where(RepairOrder.vehicle_id.in_(ids or [-1]))
    if current.role == "driver":
        rs = await db.execute(select(Vehicle.id).where(Vehicle.driver_id == current.id))
        ids = [r[0] for r in rs]
        return query.where(RepairOrder.vehicle_id.in_(ids or [-1]))
    if current.role == "repair_shop":
        return query.where(RepairOrder.assigned_to == current.id)
    raise HTTPException(403, "无权访问维修单")


async def ensure_repair_access(db: AsyncSession, current: User, order: RepairOrder):
    if not order:
        raise HTTPException(404, "维修单不存在")
    if current.role == "admin":
        return
    if current.role == "repair_shop" and order.assigned_to == current.id:
        return
    vehicle = await db.get(Vehicle, order.vehicle_id)
    await ensure_vehicle_access(db, current, vehicle)


async def scoped_inspection_query(query, current: User, db: AsyncSession):
    if current.role == "admin":
        return query
    if is_manager(current):
        ensure_group_user(current)
        rs = await db.execute(select(Vehicle.id).where(Vehicle.group_id == current.group_id))
        ids = [r[0] for r in rs]
        return query.where(Inspection.vehicle_id.in_(ids or [-1]))
    if current.role == "driver":
        return query.where(Inspection.driver_id == current.id)
    raise HTTPException(403, "无权访问日检")
''', encoding='utf-8')

(base/'路由/group_user.py').write_text(r'''"""分组 & 用户管理"""
import openpyxl
from io import BytesIO
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel
from database import get_db
from 模型.user import Group, User
from 服务.auth import hash_password, get_current_user, require_role
from 服务.permissions import is_manager, ensure_group_user, check_username, check_password, check_phone, norm_role, scoped_user_query

router = APIRouter(prefix="/api", tags=["分组&用户"])

class GroupReq(BaseModel):
    name: str
    desc: str = ""

@router.get("/groups")
async def list_groups(db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    query = select(Group).order_by(Group.id)
    if is_manager(user):
        ensure_group_user(user)
        query = query.where(Group.id == user.group_id)
    elif user.role not in ("admin", "driver"):
        query = query.where(Group.id == -1)
    elif user.role == "driver":
        query = query.where(Group.id == user.group_id)
    result = await db.execute(query)
    groups = result.scalars().all()
    return [{"id": g.id, "name": g.name, "desc": g.desc, "member_count": len(g.users), "vehicle_count": len(g.vehicles)} for g in groups]

@router.post("/groups")
async def create_group(req: GroupReq, db: AsyncSession = Depends(get_db), user: User = Depends(require_role("admin"))):
    if not req.name.strip():
        raise HTTPException(400, "分组名称不能为空")
    g = Group(name=req.name.strip(), desc=req.desc)
    db.add(g)
    await db.commit()
    await db.refresh(g)
    return {"id": g.id, "name": g.name, "desc": g.desc}

@router.put("/groups/{gid}")
async def update_group(gid: int, req: GroupReq, db: AsyncSession = Depends(get_db), user: User = Depends(require_role("admin"))):
    g = await db.get(Group, gid)
    if not g:
        raise HTTPException(404, "分组不存在")
    g.name = req.name.strip()
    g.desc = req.desc
    await db.commit()
    return {"msg": "已更新"}

@router.delete("/groups/{gid}")
async def delete_group(gid: int, db: AsyncSession = Depends(get_db), user: User = Depends(require_role("admin"))):
    g = await db.get(Group, gid)
    if not g:
        raise HTTPException(404, "分组不存在")
    if g.users or g.vehicles:
        raise HTTPException(400, "分组下还有人员或车辆，无法删除")
    await db.delete(g)
    await db.commit()
    return {"msg": "已删除"}

class UserReq(BaseModel):
    username: str
    password: str = ""
    name: str
    phone: str = ""
    role: str = "driver"
    group_id: int | None = None


def user_dict(u: User):
    return {"id": u.id, "username": u.username, "name": u.name, "phone": u.phone, "role": u.role, "group_id": u.group_id, "group_name": u.group.name if u.group else "", "is_active": u.is_active}

@router.get("/users")
async def list_users(role: str | None = None, q: str | None = None, db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    query = select(User).order_by(User.id)
    query = await scoped_user_query(query, user)
    if role:
        query = query.where(User.role == norm_role(role))
    if q:
        like = f"%{q}%"
        query = query.where((User.username.like(like)) | (User.name.like(like)) | (User.phone.like(like)))
    result = await db.execute(query)
    return [user_dict(u) for u in result.scalars().all()]

@router.get("/users/{uid}")
async def get_user(uid: int, db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    target = await db.get(User, uid)
    if not target:
        raise HTTPException(404, "用户不存在")
    if user.role != "admin":
        if is_manager(user):
            ensure_group_user(user)
            if target.group_id != user.group_id:
                raise HTTPException(403, "只能查看自己分组的用户")
        elif target.id != user.id:
            raise HTTPException(403, "只能查看自己")
    return user_dict(target)

@router.post("/users")
async def create_user(req: UserReq, db: AsyncSession = Depends(get_db), user: User = Depends(require_role("admin", "fleet_manager", "manager", "dispatcher"))):
    req.role = norm_role(req.role)
    check_username(req.username)
    check_password(req.password or "123456", required=True)
    check_phone(req.phone)
    if req.role not in ("admin", "fleet_manager", "repair_shop", "driver"):
        raise HTTPException(400, "无效的角色")
    if is_manager(user):
        ensure_group_user(user)
        if req.role not in ("driver",):
            raise HTTPException(403, "车管员只能添加驾驶员")
        req.group_id = user.group_id
    exist = await db.execute(select(User).where(User.username == req.username))
    if exist.first():
        raise HTTPException(400, "用户名已存在")
    u = User(username=req.username, password_hash=hash_password(req.password or "123456"), name=req.name, phone=req.phone, role=req.role, group_id=req.group_id)
    db.add(u)
    await db.commit()
    await db.refresh(u)
    return user_dict(u)

@router.put("/users/{uid}")
async def update_user(uid: int, req: UserReq, db: AsyncSession = Depends(get_db), user: User = Depends(require_role("admin", "fleet_manager", "manager", "dispatcher"))):
    u = await db.get(User, uid)
    if not u:
        raise HTTPException(404, "用户不存在")
    check_phone(req.phone)
    check_password(req.password, required=False)
    req.role = norm_role(req.role)
    if is_manager(user):
        ensure_group_user(user)
        if u.group_id != user.group_id:
            raise HTTPException(403, "只能管理自己分组的用户")
        if u.role not in ("driver",) or req.role not in ("driver",):
            raise HTTPException(403, "车管员只能修改自己分组驾驶员")
        u.group_id = user.group_id
    else:
        if req.role not in ("admin", "fleet_manager", "repair_shop", "driver"):
            raise HTTPException(400, "无效的角色")
        u.role = req.role
        u.group_id = req.group_id
    u.name = req.name
    u.phone = req.phone
    if req.password:
        u.password_hash = hash_password(req.password)
    await db.commit()
    return {"msg": "已更新"}

@router.delete("/users/{uid}")
async def delete_user(uid: int, db: AsyncSession = Depends(get_db), user: User = Depends(require_role("admin"))):
    u = await db.get(User, uid)
    if not u:
        raise HTTPException(404, "用户不存在")
    if u.role == "admin":
        result = await db.execute(select(User).where(User.role == "admin"))
        if len(result.scalars().all()) <= 1:
            raise HTTPException(400, "至少保留一个管理员账号")
    await db.delete(u)
    await db.commit()
    return {"msg": "已删除"}

@router.post("/users/import")
async def import_users(items: list[UserReq], db: AsyncSession = Depends(get_db), user: User = Depends(require_role("admin", "fleet_manager", "manager", "dispatcher"))):
    imported = skipped = 0
    errors = []
    for idx, req in enumerate(items, start=1):
        try:
            req.role = norm_role(req.role or "driver")
            check_username(req.username); check_password(req.password or "123456", True); check_phone(req.phone)
            if is_manager(user):
                if req.role != "driver":
                    raise HTTPException(403, "车管员只能导入驾驶员")
                req.group_id = user.group_id
            exists = await db.execute(select(User).where(User.username == req.username))
            if exists.first():
                skipped += 1; continue
            db.add(User(username=req.username, password_hash=hash_password(req.password or "123456"), name=req.name or req.username, phone=req.phone, role=req.role, group_id=req.group_id))
            imported += 1
        except Exception as e:
            skipped += 1; errors.append(f"第{idx}行: {getattr(e, 'detail', str(e))}")
    await db.commit()
    return {"imported": imported, "skipped": skipped, "errors": errors}

@router.post("/users/import/xlsx")
async def import_users_xlsx(file: UploadFile = File(...), db: AsyncSession = Depends(get_db), user: User = Depends(require_role("admin", "fleet_manager", "manager", "dispatcher"))):
    if not file.filename.endswith((".xlsx", ".xls")):
        raise HTTPException(400, "请上传 .xlsx/.xls 文件")
    wb = openpyxl.load_workbook(BytesIO(await file.read()))
    ws = wb.active
    items = []
    for row in ws.iter_rows(min_row=2, values_only=True):
        if not row or not row[0]:
            continue
        items.append(UserReq(username=str(row[0]).strip(), name=str(row[1] or row[0]).strip(), role=str(row[2] or "driver").strip(), phone=str(row[3] or "").strip(), password=str(row[4] or "123456").strip(), group_id=int(row[5]) if len(row) > 5 and row[5] else None))
    return await import_users(items, db, user)
''', encoding='utf-8')
print('patched permissions and group_user')
