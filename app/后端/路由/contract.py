"""合同管理"""
import logging
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from pydantic import BaseModel
from database import get_db
from models.contract import Contract
from models.user import User
from services.auth import get_current_user, require_role
from services.operation_log import log_operation

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/contracts", tags=["合同"])


class ContractReq(BaseModel):
    name: str = ""
    notes: str = ""


@router.get("")
async def list_contracts(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    result = await db.execute(select(Contract).order_by(desc(Contract.id)))
    contracts = result.scalars().all()
    return [
        {
            "id": c.id,
            "name": c.name,
            "notes": c.notes,
            "is_active": c.is_active,
            "created_at": c.created_at.isoformat() if c.created_at else None,
        }
        for c in contracts
    ]


@router.post("")
async def create_contract(
    req: ContractReq,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_role("admin")),
):
    c = Contract(name=req.name, notes=req.notes)
    db.add(c)
    await db.commit()
    await db.refresh(c)
    await log_operation(db, user, f"创建了合同「{c.name}」", "contract", c.id)
    return {"id": c.id, "name": c.name}


@router.put("/{cid}")
async def update_contract(
    cid: int,
    req: ContractReq,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_role("admin")),
):
    c = await db.get(Contract, cid)
    if not c:
        raise HTTPException(404, "合同不存在")
    c.name = req.name
    c.notes = req.notes
    await db.commit()
    await log_operation(db, user, f"编辑了合同「{c.name}」", "contract", cid)
    return {"msg": "已更新"}


@router.delete("/{cid}")
async def delete_contract(
    cid: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_role("admin")),
):
    c = await db.get(Contract, cid)
    if not c:
        raise HTTPException(404, "合同不存在")
    await log_operation(db, user, f"删除了合同「{c.name}」", "contract", cid)
    await db.delete(c)
    await db.commit()
    return {"msg": "已删除"}


@router.post("/{cid}/activate")
async def activate_contract(
    cid: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_role("admin")),
):
    """启用指定合同（自动停用其他合同）"""
    c = await db.get(Contract, cid)
    if not c:
        raise HTTPException(404, "合同不存在")
    # 先停用所有合同
    all_c = await db.execute(select(Contract))
    for contract in all_c.scalars().all():
        contract.is_active = False
    # 再启用指定合同
    c.is_active = True
    await db.commit()
    await log_operation(db, user, f"启用了合同「{c.name}」", "contract", cid)
    return {"id": c.id, "name": c.name, "is_active": True}
