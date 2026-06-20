from pathlib import Path
p=Path('/vol1/@appcenter/vehicle-mgr/后端/路由/contract_part.py')
s=p.read_text(encoding='utf-8')
if '@router.get("/models")' not in s:
    insert=r'''

@router.get("/models")
async def list_contract_models(shop_id: int | None = None, db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    """获取合同中已录入的车型列表；修理厂只能看自己的车型"""
    query = select(ContractPart.vehicle_model).where(ContractPart.vehicle_model != "")
    if user.role == "repair_shop":
        query = query.where(ContractPart.shop_id == user.id)
    elif shop_id:
        query = query.where(ContractPart.shop_id == shop_id)
    rs = await db.execute(query)
    models = sorted({r[0] for r in rs if r[0]})
    return [{"model": m} for m in models]
'''
    s=s.replace('\n@router.get("")', insert+'\n@router.get("")')
p.write_text(s,encoding='utf-8')
print('contract models api patched')
