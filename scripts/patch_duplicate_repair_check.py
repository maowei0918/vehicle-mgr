from pathlib import Path
base=Path('/vol1/@appcenter/vehicle-mgr/后端')

p=base/'路由/repair.py'
s=p.read_text(encoding='utf-8')

old='''    if not vehicle:
        raise HTTPException(404, "车辆不存在")
    await ensure_vehicle_access(db, user, vehicle)
    assigned_to = req.assigned_to or req.shop_id'''
new='''    if not vehicle:
        raise HTTPException(404, "车辆不存在")
    await ensure_vehicle_access(db, user, vehicle)
    # 检查该车辆是否有未完成的维修单
    active_statuses = {"dispatched", "accepted", "submitted", "in_progress", "completed"}
    dup = await db.execute(
        select(RepairOrder.id).where(
            RepairOrder.vehicle_id == vehicle.id,
            RepairOrder.status.in_(active_statuses)
        ).limit(1)
    )
    if dup.scalar_one_or_none():
        raise HTTPException(400, "该车辆有未完成的维修单，请先完成或撤回后再发起")
    assigned_to = req.assigned_to or req.shop_id'''
if old in s:
    s=s.replace(old,new)
else:
    print('WARN dispatch check block not matched')
p.write_text(s,encoding='utf-8')
print('duplicate repair check patched')
