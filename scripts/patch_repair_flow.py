from pathlib import Path
base=Path('/vol1/@appcenter/vehicle-mgr/后端')
p=base/'路由/repair.py'
s=p.read_text(encoding='utf-8')
s=s.replace('from 模型.repair import RepairOrder, RepairDetail, WarrantyAlert', 'from 模型.repair import RepairOrder, RepairDetail, WarrantyAlert, ContractPart')
# enrich detail req comment, compatible list dict already enough
s=s.replace('''class DetailReq(BaseModel):
    """汽修厂上传维修明细"""
    items: list[dict]  # [{item_name, item_desc, parts_used, cost, warranty_days}]
    photos: str = "[]"''', '''class DetailReq(BaseModel):
    """汽修厂上传维修明细"""
    # [{item_name, part_model/item_desc, quantity, unit_price/cost, warranty_days, parts_used}]
    items: list[dict]
    photos: str = "[]"''')
# status return list include assigned_to and photos
s=s.replace('''            "shop_name": o.shop_name,
            "description": o.description,
            "status": o.status,''', '''            "shop_name": o.shop_name,
            "assigned_to": o.assigned_to,
            "description": o.description,
            "status": o.status,''')
s=s.replace('''        "shop_name": order.shop_name,
        "description": order.description,''', '''        "shop_name": order.shop_name,
        "assigned_to": order.assigned_to,
        "description": order.description,''')
# detail dict add contract flag from item_desc marker
old='''        "details": [{
            "id": d.id, "item_name": d.item_name, "item_desc": d.item_desc,
            "parts_used": d.parts_used, "cost": d.cost,
            "warranty_days": d.warranty_days, "warranty_end": d.warranty_end,
        } for d in order.details],'''
new='''        "details": [{
            "id": d.id, "item_name": d.item_name, "item_desc": d.item_desc,
            "parts_used": d.parts_used, "cost": d.cost,
            "warranty_days": d.warranty_days, "warranty_end": d.warranty_end,
            "is_contract_item": "【非合同配件】" not in (d.item_desc or ""),
            "contract_warning": "该配件不在合同配件明细内" if "【非合同配件】" in (d.item_desc or "") else "",
        } for d in order.details],'''
s=s.replace(old,new)
# accept must ensure assigned to current shop, don't overwrite if assigned to another
s=s.replace('''    if order.status != "dispatched":
        raise HTTPException(400, "当前状态不可接单")
    order.status = "accepted"
    order.assigned_to = user.id
    order.accept_photos = req.accept_photos''', '''    if order.status != "dispatched":
        raise HTTPException(400, "当前状态不可接单")
    if order.assigned_to and order.assigned_to != user.id:
        raise HTTPException(403, "该维修单未指派给当前修理厂")
    order.status = "accepted"
    order.assigned_to = user.id
    order.accept_photos = req.accept_photos''')
# upload_details status submitted, check assigned, contract check
old='''    if order.status not in ("accepted", "in_progress"):
        raise HTTPException(400, "当前状态不可上传明细")

    order.status = "in_progress"

    # 删除旧明细'''
new='''    if order.assigned_to and order.assigned_to != user.id:
        raise HTTPException(403, "该维修单未指派给当前修理厂")
    if order.status not in ("accepted", "in_progress", "submitted"):
        raise HTTPException(400, "当前状态不可上传明细")

    order.status = "submitted"
    order.accept_photos = req.photos or order.accept_photos

    # 删除旧明细'''
s=s.replace(old,new)
old='''        detail = RepairDetail(
            order_id=oid,
            item_name=item["item_name"],
            item_desc=item.get("item_desc", ""),
            parts_used=item.get("parts_used", ""),
            cost=item.get("cost", 0),
            warranty_days=item.get("warranty_days", 0),
            warranty_end=warranty_end,
            photos=req.photos,
        )'''
new='''        part_name = item.get("item_name", "").strip()
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
        cost = item.get("cost", item.get("unit_price", 0))
        detail = RepairDetail(
            order_id=oid,
            item_name=part_name,
            item_desc=desc,
            parts_used=item.get("parts_used", ""),
            cost=cost,
            warranty_days=item.get("warranty_days", cp.warranty_days if cp else 0),
            warranty_end=warranty_end,
            photos=req.photos,
        )'''
s=s.replace(old,new)
s=s.replace('''        await _check_warranty(db, oid, order.vehicle_id, item["item_name"], warranty_end)''', '''        await _check_warranty(db, oid, order.vehicle_id, part_name, warranty_end)''')
s=s.replace('''    return {"msg": "明细已上传"}''', '''    return {"msg": "明细已上传", "status": "submitted"}''')
# complete allow submitted too
s=s.replace('''    if order.status not in ("in_progress", "accepted"):
        raise HTTPException(400, "当前状态不可完成")''', '''    if order.status not in ("in_progress", "accepted", "submitted"):
        raise HTTPException(400, "当前状态不可完成")''')
p.write_text(s,encoding='utf-8')
print('repair flow patched')
