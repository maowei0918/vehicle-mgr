from pathlib import Path
base = Path('/vol1/@appcenter/vehicle-mgr/后端')

p = base/'路由/repair.py'
s = p.read_text(encoding='utf-8')
# inject imports
s = s.replace('from 服务.auth import get_current_user, require_role', 'from 服务.auth import get_current_user, require_role\nfrom 服务.permissions import is_manager, ensure_vehicle_access, scoped_repair_query, ensure_repair_access')
# allow plate_number dispatch payload by replacing DispatchReq class
old = '''class DispatchReq(BaseModel):\n    """车管员派单"""\n    vehicle_id: int\n    description: str = ""\n    shop_name: str = ""\n    assigned_to: int | None = None\n    dispatch_photos: str = "[]"'''
new = '''class DispatchReq(BaseModel):\n    """车管员派单"""\n    vehicle_id: int | None = None\n    plate_number: str = ""\n    description: str = ""\n    shop_name: str = ""\n    assigned_to: int | None = None\n    shop_id: int | None = None\n    dispatch_photos: str = "[]"'''
s = s.replace(old, new)
# add compatibility create endpoint before dispatch
marker='''@router.post("/dispatch")'''
compat = r'''
@router.post("")
async def create_repair_compat(req: DispatchReq, db: AsyncSession = Depends(get_db),
                               user: User = Depends(require_role("fleet_manager", "manager", "dispatcher", "admin", "driver"))):
    """兼容后台表单：通过车牌号+维修厂创建维修单"""
    return await dispatch_repair(req, db, user)

'''
s = s.replace(marker, compat + marker)
# replace dispatch function body portion
old_body = '''    """车管员派单"""
    vehicle = await db.get(Vehicle, req.vehicle_id)
    if not vehicle:
        raise HTTPException(404, "车辆不存在")
    order = RepairOrder(
        vehicle_id=req.vehicle_id,
        created_by=user.id,
        assigned_to=req.assigned_to,
        shop_name=req.shop_name,
        description=req.description,
        dispatch_photos=req.dispatch_photos,
        status="dispatched",
    )'''
new_body = '''    """车管员派单"""
    vehicle = None
    if req.vehicle_id:
        vehicle = await db.get(Vehicle, req.vehicle_id)
    elif req.plate_number:
        rs = await db.execute(select(Vehicle).where(Vehicle.plate_number == req.plate_number))
        vehicle = rs.scalar_one_or_none()
    if not vehicle:
        raise HTTPException(404, "车辆不存在")
    await ensure_vehicle_access(db, user, vehicle)
    assigned_to = req.assigned_to or req.shop_id
    shop_name = req.shop_name
    if assigned_to:
        shop = await db.get(User, assigned_to)
        if not shop or shop.role != "repair_shop":
            raise HTTPException(400, "请选择有效的修理厂")
        shop_name = shop.name
    order = RepairOrder(
        vehicle_id=vehicle.id,
        created_by=user.id,
        assigned_to=assigned_to,
        shop_name=shop_name,
        description=req.description,
        dispatch_photos=req.dispatch_photos,
        status="dispatched",
    )'''
s = s.replace(old_body, new_body)
# replace list scope logic block
old_scope = '''    if user.role == "fleet_manager" and user.group_id:
        vehs = await db.execute(select(Vehicle.id).where(Vehicle.group_id == user.group_id))
        vids = [r[0] for r in vehs]
        query = query.where(RepairOrder.vehicle_id.in_(vids))
    elif user.role == "driver":
        vehs = await db.execute(select(Vehicle.id).where(Vehicle.driver_id == user.id))
        vids = [r[0] for r in vehs]
        query = query.where(RepairOrder.vehicle_id.in_(vids))
    elif user.role == "repair_shop":
        query = query.where(RepairOrder.assigned_to == user.id)
'''
s = s.replace(old_scope, '    query = await scoped_repair_query(query, user, db)\n')
# add access check to get_repair after vehicle line
s = s.replace('''    vehicle = await db.get(Vehicle, order.vehicle_id)
    return {''', '''    vehicle = await db.get(Vehicle, order.vehicle_id)
    await ensure_repair_access(db, user, order)
    return {''')
p.write_text(s, encoding='utf-8')

# patch inspection access
p = base/'路由/inspection.py'
s = p.read_text(encoding='utf-8')
s = s.replace('from 服务.auth import get_current_user, require_role', 'from 服务.auth import get_current_user, require_role\nfrom 服务.permissions import ensure_vehicle_access, scoped_inspection_query')
s = s.replace('''    # 查询上次里程''', '''    await ensure_vehicle_access(db, user, vehicle)

    # 查询上次里程''')
old = '''    if user.role == "fleet_manager" and user.group_id:
        # 只查自己分组的车辆日检
        vehs = await db.execute(select(Vehicle.id).where(Vehicle.group_id == user.group_id))
        vids = [r[0] for r in vehs]
        query = query.where(Inspection.vehicle_id.in_(vids))
    elif user.role == "driver":
        query = query.where(Inspection.driver_id == user.id)
'''
s = s.replace(old, '    query = await scoped_inspection_query(query, user, db)\n')
p.write_text(s, encoding='utf-8')
print('repair/inspection patched')
