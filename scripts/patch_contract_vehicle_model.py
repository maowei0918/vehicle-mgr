from pathlib import Path
base=Path('/vol1/@appcenter/vehicle-mgr/后端')

# 1) model add vehicle_model column
p=base/'模型/repair.py'
s=p.read_text(encoding='utf-8')
if 'vehicle_model:' not in s:
    s=s.replace('''    part_name: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    part_model: Mapped[str] = mapped_column(String(128), default="")''', '''    vehicle_model: Mapped[str] = mapped_column(String(128), default="", index=True)
    part_name: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    part_model: Mapped[str] = mapped_column(String(128), default="")''')
p.write_text(s,encoding='utf-8')

# 2) router contract_part add vehicle_model
p=base/'路由/contract_part.py'
s=p.read_text(encoding='utf-8')
s=s.replace('''class ContractPartReq(BaseModel):
    shop_id: int | None = None
    part_name: str''', '''class ContractPartReq(BaseModel):
    shop_id: int | None = None
    vehicle_model: str = ""
    part_name: str''')
s=s.replace('''return {"id": cp.id, "shop_id": cp.shop_id, "part_name": cp.part_name,''', '''return {"id": cp.id, "shop_id": cp.shop_id, "vehicle_model": cp.vehicle_model, "part_name": cp.part_name,''')
s=s.replace('''# 支持列：修理厂ID,配件名称,型号,合同价,质保天数,备注
            shop_id=int(row[0]) if row[0] else None
            cp=ContractPart(shop_id=shop_id, part_name=str(row[1] or '').strip(), part_model=str(row[2] or '').strip(), contract_price=float(row[3] or 0), warranty_days=int(row[4] or 0), notes=str(row[5] or '').strip())''', '''# 支持列：修理厂ID,车型,配件名称,型号,合同价,质保天数,备注
            shop_id=int(row[0]) if row[0] else None
            cp=ContractPart(shop_id=shop_id, vehicle_model=str(row[1] or '').strip(), part_name=str(row[2] or '').strip(), part_model=str(row[3] or '').strip(), contract_price=float(row[4] or 0), warranty_days=int(row[5] or 0), notes=str(row[6] or '').strip())''')
p.write_text(s,encoding='utf-8')

# 3) repair check: first vehicle model, then part under model
p=base/'路由/repair.py'
s=p.read_text(encoding='utf-8')
old='''        part_name = item.get("item_name", "").strip()
        part_model = (item.get("part_model") or item.get("item_desc") or "").strip()
        q = select(ContractPart).where(ContractPart.part_name == part_name)
        if order.assigned_to:
            q = q.where(ContractPart.shop_id == order.assigned_to)
        if part_model:
            q = q.where(ContractPart.part_model == part_model)
        cp = (await db.execute(q.limit(1))).scalar_one_or_none()
        is_contract = cp is not None
        desc = part_model
        if not is_contract:
            desc = ("【非合同配件】" + desc).strip()
        cost = item.get("cost", item.get("unit_price", 0))'''
new='''        part_name = item.get("item_name", "").strip()
        part_model = (item.get("part_model") or item.get("item_desc") or "").strip()
        vehicle = await db.get(Vehicle, order.vehicle_id)
        vehicle_model = (vehicle.model if vehicle else "") or ""

        # 第一步：验证该修理厂合同内是否覆盖该车型
        model_q = select(ContractPart).where(ContractPart.vehicle_model == vehicle_model)
        if order.assigned_to:
            model_q = model_q.where(ContractPart.shop_id == order.assigned_to)
        model_exists = (await db.execute(model_q.limit(1))).scalar_one_or_none() is not None

        # 第二步：验证该车型下是否包含该配件
        q = select(ContractPart).where(ContractPart.vehicle_model == vehicle_model, ContractPart.part_name == part_name)
        if order.assigned_to:
            q = q.where(ContractPart.shop_id == order.assigned_to)
        if part_model:
            q = q.where(ContractPart.part_model == part_model)
        cp = (await db.execute(q.limit(1))).scalar_one_or_none()
        is_contract = cp is not None
        desc = part_model
        if not model_exists:
            desc = ("【车型不在合同内】" + desc).strip()
        elif not is_contract:
            desc = ("【非合同配件】" + desc).strip()
        cost = item.get("cost", item.get("unit_price", 0))'''
if old in s:
    s=s.replace(old,new)
else:
    print('WARN: repair check block not found')
s=s.replace('''"is_contract_item": "【非合同配件】" not in (d.item_desc or ""),
            "contract_warning": "该配件不在合同配件明细内" if "【非合同配件】" in (d.item_desc or "") else "",''', '''"is_contract_item": ("【非合同配件】" not in (d.item_desc or "") and "【车型不在合同内】" not in (d.item_desc or "")),
            "contract_warning": "车型不在该修理厂合同内" if "【车型不在合同内】" in (d.item_desc or "") else ("该车型下该配件不在合同配件明细内" if "【非合同配件】" in (d.item_desc or "") else ""),''')
p.write_text(s,encoding='utf-8')
print('vehicle model contract patch done')
