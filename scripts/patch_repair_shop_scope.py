from pathlib import Path
base=Path('/vol1/@appcenter/vehicle-mgr/后端')

# permissions: repair_shop can NEVER see vehicles/users/groups/inspections
p=base/'服务/permissions.py'
s=p.read_text(encoding='utf-8')
s=s.replace(
'''async def scoped_vehicle_query(query, current: User):
    if current.role == "admin":
        return query
    if is_manager(current):
        ensure_group_user(current)
        return query.where(Vehicle.group_id == current.group_id)
    if current.role == "driver":
        return query.where(Vehicle.driver_id == current.id)
    raise HTTPException(403, "无权访问车辆")''',
'''async def scoped_vehicle_query(query, current: User):
    if current.role == "admin":
        return query
    if is_manager(current):
        ensure_group_user(current)
        return query.where(Vehicle.group_id == current.group_id)
    if current.role == "driver":
        return query.where(Vehicle.driver_id == current.id)
    if current.role == "repair_shop":
        raise HTTPException(403, "无权访问车辆")
    raise HTTPException(403, "无权访问车辆")'''
)
s=s.replace(
'''async def scoped_inspection_query(query, current: User, db: AsyncSession):
    if current.role == "admin":
        return query
    if is_manager(current):
        ensure_group_user(current)
        rs = await db.execute(select(Vehicle.id).where(Vehicle.group_id == current.group_id))
        ids = [r[0] for r in rs]
        return query.where(Inspection.vehicle_id.in_(ids or [-1]))
    if current.role == "driver":
        return query.where(Inspection.driver_id == current.id)
    raise HTTPException(403, "无权访问日检")''',
'''async def scoped_inspection_query(query, current: User, db: AsyncSession):
    if current.role == "admin":
        return query
    if is_manager(current):
        ensure_group_user(current)
        rs = await db.execute(select(Vehicle.id).where(Vehicle.group_id == current.group_id))
        ids = [r[0] for r in rs]
        return query.where(Inspection.vehicle_id.in_(ids or [-1]))
    if current.role == "driver":
        return query.where(Inspection.driver_id == current.id)
    if current.role == "repair_shop":
        raise HTTPException(403, "无权访问日检")
    raise HTTPException(403, "无权访问日检")'''
)
# repair_shop user list: only see self
s=s.replace(
'''async def scoped_user_query(query, current: User):
    if current.role == "admin":
        return query
    if is_manager(current):
        ensure_group_user(current)
        return query.where(User.group_id == current.group_id)
    return query.where(User.id == current.id)''',
'''async def scoped_user_query(query, current: User):
    if current.role == "admin":
        return query
    if is_manager(current):
        ensure_group_user(current)
        return query.where(User.group_id == current.group_id)
    if current.role == "repair_shop":
        return query.where(User.id == current.id)
    return query.where(User.id == current.id)'''
)
p.write_text(s,encoding='utf-8')

# repair.py scoped_repair_query: repair_shop only assigned_to self AND only non-completed? No - all assigned_to self is fine.
# But also need to block repair_shop from seeing other repair shops' accepted orders. Already done by assigned_to filter.
# However repair_shop should NOT see the full vehicle list when creating details etc. That is handled by ensure_repair_access.

# user.py: add shop_name field so multiple repair accounts can share one shop identity
p=base/'模型/user.py'
s=p.read_text(encoding='utf-8')
if 'shop_name' not in s:
    s=s.replace(
'''    group_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("groups.id"), nullable=True)''',
'''    group_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("groups.id"), nullable=True)
    shop_name: Mapped[str | None] = mapped_column(String(128), nullable=True, index=True)  # 修理厂名称，同一厂可建多个账号'''
    )
p.write_text(s,encoding='utf-8')

# db migration add shop_name
p=base/'database.py'
s=p.read_text(encoding='utf-8')
if 'shop_name' not in s:
    old='''        try:
            await conn.exec_driver_sql("ALTER TABLE contract_parts ADD COLUMN labor_fee FLOAT DEFAULT 0")
        except Exception:
            pass'''
    new='''        try:
            await conn.exec_driver_sql("ALTER TABLE users ADD COLUMN shop_name VARCHAR(128) DEFAULT NULL")
        except Exception:
            pass
        try:
            await conn.exec_driver_sql("CREATE INDEX ix_users_shop_name ON users (shop_name)")
        except Exception:
            pass
        try:
            await conn.exec_driver_sql("ALTER TABLE contract_parts ADD COLUMN labor_fee FLOAT DEFAULT 0")
        except Exception:
            pass'''
    s=s.replace(old,new)
p.write_text(s,encoding='utf-8')

# group_user.py: when creating repair_shop, allow shop_name; list repair_shop users by shop_name
p=base/'路由/group_user.py'
s=p.read_text(encoding='utf-8')
if 'shop_name' not in s:
    s=s.replace(
'''class UserReq(BaseModel):
    username: str
    password: str = ""
    role: str = "driver"
    phone: str = ""
    group_id: int | None = None
    is_active: bool = True''',
'''class UserReq(BaseModel):
    username: str
    password: str = ""
    role: str = "driver"
    phone: str = ""
    group_id: int | None = None
    shop_name: str = ""
    is_active: bool = True'''
    )
    s=s.replace(
'''        u = User(**req.model_dump())''',
'''        data = req.model_dump()
        if data.get("role") == "repair_shop" and not data.get("shop_name"):
            data["shop_name"] = data.get("username")
        u = User(**data)'''
    )
    s=s.replace(
'''    return {"id": u.id, "username": u.username, "role": u.role, "phone": u.phone, "group_id": u.group_id, "is_active": u.is_active, "created_at": str(u.created_at)}''',
'''    return {"id": u.id, "username": u.username, "role": u.role, "phone": u.phone, "group_id": u.group_id, "shop_name": u.shop_name, "is_active": u.is_active, "created_at": str(u.created_at)}'''
    )
    s=s.replace(
'''    for k, v in req.model_dump().items():
        setattr(u, k, v)''',
'''    data = req.model_dump()
    if data.get("role") == "repair_shop" and not data.get("shop_name"):
        data["shop_name"] = u.username
    for k, v in data.items():
        setattr(u, k, v)'''
    )
    # list: repair_shop can see all repair_shop users with same shop_name; admin sees all
    s=s.replace(
'''    if current.role == "admin":
        query = select(User).order_by(User.id.desc())
    elif is_manager(current):
        query = select(User).where(User.group_id == current.group_id).order_by(User.id.desc())
    else:
        query = select(User).where(User.id == current.id).order_by(User.id.desc())''',
'''    if current.role == "admin":
        query = select(User).order_by(User.id.desc())
    elif is_manager(current):
        query = select(User).where(User.group_id == current.group_id).order_by(User.id.desc())
    elif current.role == "repair_shop":
        query = select(User).where(User.role == "repair_shop", User.shop_name == current.shop_name).order_by(User.id.desc())
    else:
        query = select(User).where(User.id == current.id).order_by(User.id.desc())'''
    )
    # when admin lists repair_shop users for dropdown in repair form, also show shop_name
    # GET /api/users?role=repair_shop returns all repair_shop users (admin only) - fine
p.write_text(s,encoding='utf-8')

# repair.py: repair_shop can only update its own assigned orders, and only specific fields
p=base/'路由/repair.py'
s=p.read_text(encoding='utf-8')
# ensure_repair_access already blocks others. Add: repair_shop can only modify own orders and only when in accepted/submitted/in_progress
old_ensure='''async def ensure_repair_access(db: AsyncSession, current: User, order: RepairOrder):
    if not order:
        raise HTTPException(404, "维修单不存在")
    if current.role == "admin":
        return
    if current.role == "repair_shop" and order.assigned_to == current.id:
        return
    vehicle = await db.get(Vehicle, order.vehicle_id)
    await ensure_vehicle_access(db, current, vehicle)'''
new_ensure='''async def ensure_repair_access(db: AsyncSession, current: User, order: RepairOrder):
    if not order:
        raise HTTPException(404, "维修单不存在")
    if current.role == "admin":
        return
    if is_manager(current):
        vehicle = await db.get(Vehicle, order.vehicle_id)
        await ensure_vehicle_access(db, current, vehicle)
        return
    if current.role == "repair_shop":
        if order.assigned_to != current.id:
            raise HTTPException(403, "无权访问该维修单")
        return
    if current.role == "driver":
        vehicle = await db.get(Vehicle, order.vehicle_id)
        if vehicle and vehicle.driver_id == current.id:
            return
    raise HTTPException(403, "无权访问该维修单")'''
if old_ensure in s:
    s=s.replace(old_ensure,new_ensure)
else:
    print('WARN ensure_repair_access not matched')
p.write_text(s,encoding='utf-8')

print('permissions + repair_shop multi-account patched')
