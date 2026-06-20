from pathlib import Path
p=Path('/vol1/@appcenter/vehicle-mgr/后端/database.py')
s=p.read_text(encoding='utf-8')
old='''    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)'''
new='''    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        # 轻量迁移：旧库已有 contract_parts 时补 vehicle_model 字段
        try:
            await conn.exec_driver_sql("ALTER TABLE contract_parts ADD COLUMN vehicle_model VARCHAR(128) DEFAULT ''")
        except Exception:
            pass
        try:
            await conn.exec_driver_sql("CREATE INDEX ix_contract_parts_vehicle_model ON contract_parts (vehicle_model)")
        except Exception:
            pass'''
if old in s:
    s=s.replace(old,new)
p.write_text(s,encoding='utf-8')
print('db migration patched')
