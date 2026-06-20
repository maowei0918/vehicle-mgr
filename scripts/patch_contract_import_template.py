from pathlib import Path
base=Path('/vol1/@appcenter/vehicle-mgr/后端')

# model add labor_fee total_amount
p=base/'模型/repair.py'
s=p.read_text(encoding='utf-8')
if 'labor_fee' not in s:
    s=s.replace('''    contract_price: Mapped[float] = mapped_column(Float, default=0)
    warranty_days: Mapped[int] = mapped_column(Integer, default=0)''', '''    contract_price: Mapped[float] = mapped_column(Float, default=0)  # 配件价格
    labor_fee: Mapped[float] = mapped_column(Float, default=0)  # 工时费
    total_amount: Mapped[float] = mapped_column(Float, default=0)  # 合计金额
    warranty_days: Mapped[int] = mapped_column(Integer, default=0)''')
p.write_text(s,encoding='utf-8')

# db migration add cols
p=base/'database.py'
s=p.read_text(encoding='utf-8')
if 'contract_parts ADD COLUMN labor_fee' not in s:
    marker='''        try:
            await conn.exec_driver_sql("ALTER TABLE repair_orders ADD COLUMN vehicle_model_snapshot VARCHAR(128) DEFAULT ''")
        except Exception:
            pass'''
    add='''        try:
            await conn.exec_driver_sql("ALTER TABLE repair_orders ADD COLUMN vehicle_model_snapshot VARCHAR(128) DEFAULT ''")
        except Exception:
            pass
        try:
            await conn.exec_driver_sql("ALTER TABLE contract_parts ADD COLUMN labor_fee FLOAT DEFAULT 0")
        except Exception:
            pass
        try:
            await conn.exec_driver_sql("ALTER TABLE contract_parts ADD COLUMN total_amount FLOAT DEFAULT 0")
        except Exception:
            pass'''
    s=s.replace(marker,add)
p.write_text(s,encoding='utf-8')

# router update fields, template, import
p=base/'路由/contract_part.py'
s=p.read_text(encoding='utf-8')
s=s.replace('''from fastapi import APIRouter, Depends, HTTPException, UploadFile, File''','''from fastapi import APIRouter, Depends, HTTPException, UploadFile, File''')
if 'from fastapi.responses import StreamingResponse' not in s:
    s=s.replace('''import openpyxl\nfrom io import BytesIO''','''import openpyxl\nfrom io import BytesIO\nfrom fastapi.responses import StreamingResponse''')
s=s.replace('''    contract_price: float = 0\n    warranty_days: int = 0''','''    contract_price: float = 0\n    labor_fee: float = 0\n    total_amount: float = 0\n    warranty_days: int = 0''')
s=s.replace('''"contract_price": cp.contract_price, "warranty_days": cp.warranty_days''','''"contract_price": cp.contract_price, "labor_fee": cp.labor_fee, "total_amount": cp.total_amount, "warranty_days": cp.warranty_days''')
if '@router.get("/template.xlsx")' not in s:
    tpl='''\n\n@router.get("/template.xlsx")\nasync def download_contract_parts_template(user: User = Depends(require_role("admin", "fleet_manager", "manager", "dispatcher"))):\n    """下载合同配件导入模板。最低必填：车型、配件名称、配件价格、工时费、合计金额"""\n    wb = openpyxl.Workbook()\n    ws = wb.active\n    ws.title = "合同配件模板"\n    headers = ["修理厂ID", "车型", "配件名称", "配件型号", "配件价格", "工时费", "合计金额", "质保天数", "备注"]\n    ws.append(headers)\n    ws.append(["", "例：帕萨特", "例：前刹车片", "例：B7/陶瓷", 260, 80, 340, 180, "示例行，可删除"] )\n    widths = [12, 18, 22, 22, 14, 12, 14, 12, 28]\n    for i, w in enumerate(widths, start=1):\n        ws.column_dimensions[openpyxl.utils.get_column_letter(i)].width = w\n    bio = BytesIO(); wb.save(bio); bio.seek(0)\n    return StreamingResponse(\n        bio,\n        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",\n        headers={"Content-Disposition": "attachment; filename=contract_parts_template.xlsx"}\n    )\n'''
    s=s.replace('\n@router.get("/models")', tpl+'\n@router.get("/models")')
old='''    wb=openpyxl.load_workbook(BytesIO(await file.read())); ws=wb.active\n    imported=skipped=0; errors=[]\n    for idx,row in enumerate(ws.iter_rows(min_row=2, values_only=True), start=2):\n        try:\n            if not row or not row[1 if len(row)>1 else 0]: continue\n            # 支持列：修理厂ID,车型,配件名称,型号,合同价,质保天数,备注\n            shop_id=int(row[0]) if row[0] else None\n            cp=ContractPart(shop_id=shop_id, vehicle_model=str(row[1] or '').strip(), part_name=str(row[2] or '').strip(), part_model=str(row[3] or '').strip(), contract_price=float(row[4] or 0), warranty_days=int(row[5] or 0), notes=str(row[6] or '').strip())\n            db.add(cp); imported+=1\n        except Exception as e:\n            skipped+=1; errors.append(f"第{idx}行: {e}")'''
new='''    wb=openpyxl.load_workbook(BytesIO(await file.read())); ws=wb.active\n    imported=skipped=0; errors=[]\n    required = ["车型", "配件名称", "配件价格", "工时费", "合计金额"]\n    header = [str(c or '').strip() for c in next(ws.iter_rows(min_row=1, max_row=1, values_only=True))]\n    pos = {name: i for i, name in enumerate(header)}\n    missing = [x for x in required if x not in pos]\n    if missing:\n        raise HTTPException(400, "模板缺少必填列：" + "、".join(missing))\n    def val(row, name, default=''):\n        i = pos.get(name)\n        return row[i] if i is not None and i < len(row) else default\n    for idx,row in enumerate(ws.iter_rows(min_row=2, values_only=True), start=2):\n        try:\n            if not row or not any(row): continue\n            vehicle_model = str(val(row, "车型") or '').strip()\n            part_name = str(val(row, "配件名称") or '').strip()\n            if not vehicle_model or not part_name:\n                skipped += 1; errors.append(f"第{idx}行: 车型和配件名称不能为空"); continue\n            part_price = float(val(row, "配件价格", 0) or 0)\n            labor_fee = float(val(row, "工时费", 0) or 0)\n            total_amount = float(val(row, "合计金额", part_price + labor_fee) or 0)\n            shop_raw = val(row, "修理厂ID", None)\n            shop_id = int(shop_raw) if shop_raw not in (None, "") else None\n            cp=ContractPart(\n                shop_id=shop_id,\n                vehicle_model=vehicle_model,\n                part_name=part_name,\n                part_model=str(val(row, "配件型号", '') or '').strip(),\n                contract_price=part_price,\n                labor_fee=labor_fee,\n                total_amount=total_amount,\n                warranty_days=int(val(row, "质保天数", 0) or 0),\n                notes=str(val(row, "备注", '') or '').strip()\n            )\n            db.add(cp); imported+=1\n        except Exception as e:\n            skipped+=1; errors.append(f"第{idx}行: {e}")'''
if old in s:
    s=s.replace(old,new)
else:
    print('WARN import block not matched')
p.write_text(s,encoding='utf-8')
print('contract import/template backend patched')
