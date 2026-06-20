from pathlib import Path
base=Path('/vol1/@appcenter/vehicle-mgr/后端')

# model: add vehicle_model_snapshot to repair order
p=base/'模型/repair.py'
s=p.read_text(encoding='utf-8')
if 'vehicle_model_snapshot' not in s:
    s=s.replace('''    # 故障描述
    description: Mapped[str] = mapped_column(Text, default="")''', '''    # 维修单提报时选择/确认的车型快照，用于合同配件校验
    vehicle_model_snapshot: Mapped[str] = mapped_column(String(128), default="")

    # 故障描述
    description: Mapped[str] = mapped_column(Text, default="")''')
p.write_text(s,encoding='utf-8')

# db migration
p=base/'database.py'
s=p.read_text(encoding='utf-8')
if 'vehicle_model_snapshot' not in s:
    s=s.replace('''        try:
            await conn.exec_driver_sql("CREATE INDEX ix_contract_parts_vehicle_model ON contract_parts (vehicle_model)")
        except Exception:
            pass''', '''        try:
            await conn.exec_driver_sql("CREATE INDEX ix_contract_parts_vehicle_model ON contract_parts (vehicle_model)")
        except Exception:
            pass
        try:
            await conn.exec_driver_sql("ALTER TABLE repair_orders ADD COLUMN vehicle_model_snapshot VARCHAR(128) DEFAULT ''")
        except Exception:
            pass''')
p.write_text(s,encoding='utf-8')

# repair route add req field and save/read/use
p=base/'路由/repair.py'
s=p.read_text(encoding='utf-8')
s=s.replace('''    description: str = ""
    shop_name: str = ""''', '''    description: str = ""
    vehicle_model: str = ""
    shop_name: str = ""''')
s=s.replace('''        vehicle_id=vehicle.id,
        created_by=user.id,
        assigned_to=assigned_to,''', '''        vehicle_id=vehicle.id,
        created_by=user.id,
        vehicle_model_snapshot=req.vehicle_model or vehicle.model or "",
        assigned_to=assigned_to,''')
s=s.replace('''            "plate_number": vehicle.plate_number if vehicle else "",
            "shop_name": o.shop_name,''', '''            "plate_number": vehicle.plate_number if vehicle else "",
            "vehicle_model": o.vehicle_model_snapshot or (vehicle.model if vehicle else ""),
            "shop_name": o.shop_name,''')
s=s.replace('''        "plate_number": vehicle.plate_number if vehicle else "",
        "shop_name": order.shop_name,''', '''        "plate_number": vehicle.plate_number if vehicle else "",
        "vehicle_model": order.vehicle_model_snapshot or (vehicle.model if vehicle else ""),
        "shop_name": order.shop_name,''')
s=s.replace('''        vehicle = await db.get(Vehicle, order.vehicle_id)
        vehicle_model = (vehicle.model if vehicle else "") or ""''', '''        vehicle = await db.get(Vehicle, order.vehicle_id)
        vehicle_model = (order.vehicle_model_snapshot or (vehicle.model if vehicle else "")) or ""''')
p.write_text(s,encoding='utf-8')
print('repair vehicle model field patched')
