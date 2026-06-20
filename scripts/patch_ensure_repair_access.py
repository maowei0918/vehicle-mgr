from pathlib import Path
p=Path('/vol1/@appcenter/vehicle-mgr/后端/服务/permissions.py')
s=p.read_text(encoding='utf-8')
old='''async def ensure_repair_access(db: AsyncSession, current: User, order: RepairOrder):
    if not order:
        raise HTTPException(404, "维修单不存在")
    if current.role == "admin":
        return
    if current.role == "repair_shop" and order.assigned_to == current.id:
        return
    vehicle = await db.get(Vehicle, order.vehicle_id)
    await ensure_vehicle_access(db, current, vehicle)'''
new='''async def ensure_repair_access(db: AsyncSession, current: User, order: RepairOrder):
    if not order:
        raise HTTPException(404, "维修单不存在")
    if current.role == "admin":
        return
    if current.role == "repair_shop":
        if order.assigned_to != current.id:
            raise HTTPException(403, "无权访问该维修单")
        return
    if is_manager(current):
        vehicle = await db.get(Vehicle, order.vehicle_id)
        await ensure_vehicle_access(db, current, vehicle)
        return
    if current.role == "driver":
        vehicle = await db.get(Vehicle, order.vehicle_id)
        if vehicle and vehicle.driver_id == current.id:
            return
    raise HTTPException(403, "无权访问该维修单")'''
if old in s:
    s=s.replace(old,new)
else:
    print('WARN ensure_repair_access not matched')
p.write_text(s,encoding='utf-8')
print('ensure_repair_access patched')
