from pathlib import Path
base=Path('/vol1/@appcenter/vehicle-mgr/后端')

# Patch model
p=base/'模型/repair.py'
s=p.read_text(encoding='utf-8')
if 'class ContractPart' not in s:
    s += r'''

class ContractPart(Base):
    """汽修厂合同配件明细"""
    __tablename__ = "contract_parts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    shop_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("users.id"), nullable=True, index=True)
    part_name: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    part_model: Mapped[str] = mapped_column(String(128), default="")
    contract_price: Mapped[float] = mapped_column(Float, default=0)
    warranty_days: Mapped[int] = mapped_column(Integer, default=0)
    notes: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime, server_default=func.now())
'''
p.write_text(s,encoding='utf-8')

# Create router
(base/'路由/contract_part.py').write_text(r'''"""合同配件明细管理"""
import openpyxl
from io import BytesIO
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel
from database import get_db
from 模型.repair import ContractPart
from 模型.user import User
from 服务.auth import get_current_user, require_role

router = APIRouter(prefix="/api/contract-parts", tags=["合同配件"])

class ContractPartReq(BaseModel):
    shop_id: int | None = None
    part_name: str
    part_model: str = ""
    contract_price: float = 0
    warranty_days: int = 0
    notes: str = ""

def d(cp: ContractPart):
    return {"id": cp.id, "shop_id": cp.shop_id, "part_name": cp.part_name, "part_model": cp.part_model, "contract_price": cp.contract_price, "warranty_days": cp.warranty_days, "notes": cp.notes}

@router.get("")
async def list_contract_parts(shop_id: int | None = None, q: str | None = None, db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    query = select(ContractPart).order_by(ContractPart.id.desc())
    if user.role == "repair_shop":
        query = query.where(ContractPart.shop_id == user.id)
    elif shop_id:
        query = query.where(ContractPart.shop_id == shop_id)
    if q:
        query = query.where(ContractPart.part_name.like(f"%{q}%"))
    rs = await db.execute(query)
    return [d(x) for x in rs.scalars().all()]

@router.post("")
async def create_contract_part(req: ContractPartReq, db: AsyncSession = Depends(get_db), user: User = Depends(require_role("admin", "fleet_manager", "manager", "dispatcher"))):
    if not req.part_name.strip():
        raise HTTPException(400, "配件名称不能为空")
    cp = ContractPart(**req.model_dump())
    db.add(cp)
    await db.commit(); await db.refresh(cp)
    return d(cp)

@router.put("/{pid}")
async def update_contract_part(pid: int, req: ContractPartReq, db: AsyncSession = Depends(get_db), user: User = Depends(require_role("admin", "fleet_manager", "manager", "dispatcher"))):
    cp = await db.get(ContractPart, pid)
    if not cp: raise HTTPException(404, "合同配件不存在")
    for k,v in req.model_dump().items(): setattr(cp,k,v)
    await db.commit()
    return {"msg":"已更新"}

@router.delete("/{pid}")
async def delete_contract_part(pid: int, db: AsyncSession = Depends(get_db), user: User = Depends(require_role("admin", "fleet_manager", "manager", "dispatcher"))):
    cp = await db.get(ContractPart, pid)
    if not cp: raise HTTPException(404, "合同配件不存在")
    await db.delete(cp); await db.commit()
    return {"msg":"已删除"}

@router.post("/import/xlsx")
async def import_contract_parts_xlsx(file: UploadFile = File(...), db: AsyncSession = Depends(get_db), user: User = Depends(require_role("admin", "fleet_manager", "manager", "dispatcher"))):
    if not file.filename.endswith((".xlsx", ".xls")):
        raise HTTPException(400, "请上传 .xlsx/.xls 文件")
    wb=openpyxl.load_workbook(BytesIO(await file.read())); ws=wb.active
    imported=skipped=0; errors=[]
    for idx,row in enumerate(ws.iter_rows(min_row=2, values_only=True), start=2):
        try:
            if not row or not row[1 if len(row)>1 else 0]: continue
            # 支持列：修理厂ID,配件名称,型号,合同价,质保天数,备注
            shop_id=int(row[0]) if row[0] else None
            cp=ContractPart(shop_id=shop_id, part_name=str(row[1] or '').strip(), part_model=str(row[2] or '').strip(), contract_price=float(row[3] or 0), warranty_days=int(row[4] or 0), notes=str(row[5] or '').strip())
            db.add(cp); imported+=1
        except Exception as e:
            skipped+=1; errors.append(f"第{idx}行: {e}")
    await db.commit()
    return {"imported":imported,"skipped":skipped,"errors":errors}
''',encoding='utf-8')

# patch main router include
p=base/'main.py'
s=p.read_text(encoding='utf-8')
if 'contract_part' not in s:
    s=s.replace('from 路由 import auth, group_user, vehicle, inspection, repair, settings, dashboard', 'from 路由 import auth, group_user, vehicle, inspection, repair, settings, dashboard, contract_part')
    s=s.replace('app.include_router(dashboard.router)', 'app.include_router(dashboard.router)\napp.include_router(contract_part.router)')
p.write_text(s,encoding='utf-8')
print('contract parts patched')
