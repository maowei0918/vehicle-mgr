"""维修流程自定义管理"""
import logging
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from pydantic import BaseModel
from database import get_db
from models.repair_flow import RepairFlow, RepairFlowStep
from models.user import User
from services.auth import get_current_user, require_role
from services.operation_log import log_operation

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/repair-flows", tags=["维修流程"])


class FlowReq(BaseModel):
    name: str = ""


class StepReq(BaseModel):
    step_order: int = 0
    step_name: str = ""
    action_role: str = ""
    action_label: str = ""


# ====== 流程 CRUD ======

@router.get("")
async def list_flows(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    result = await db.execute(select(RepairFlow).order_by(desc(RepairFlow.id)))
    flows = result.scalars().all()
    return [
        {"id": f.id, "name": f.name, "created_at": f.created_at.isoformat() if f.created_at else None}
        for f in flows
    ]


@router.post("")
async def create_flow(
    req: FlowReq,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_role("admin")),
):
    f = RepairFlow(name=req.name or "新流程")
    db.add(f)
    await db.commit()
    await db.refresh(f)
    await log_operation(db, user, f"创建了维修流程「{f.name}」", "repair_flow", f.id)
    return {"id": f.id, "name": f.name}


@router.put("/{fid}")
async def update_flow(
    fid: int,
    req: FlowReq,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_role("admin")),
):
    f = await db.get(RepairFlow, fid)
    if not f:
        raise HTTPException(404, "流程不存在")
    f.name = req.name
    await db.commit()
    await log_operation(db, user, f"编辑了维修流程「{f.name}」", "repair_flow", fid)
    return {"msg": "已更新"}


@router.delete("/{fid}")
async def delete_flow(
    fid: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_role("admin")),
):
    f = await db.get(RepairFlow, fid)
    if not f:
        raise HTTPException(404, "流程不存在")
    await log_operation(db, user, f"删除了维修流程「{f.name}」", "repair_flow", fid)
    # 同时删除步骤
    steps = await db.execute(select(RepairFlowStep).where(RepairFlowStep.flow_id == fid))
    for s in steps.scalars().all():
        await db.delete(s)
    await db.delete(f)
    await db.commit()
    return {"msg": "已删除"}


# ====== 步骤管理 ======

@router.get("/{fid}/steps")
async def list_steps(
    fid: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(RepairFlowStep).where(RepairFlowStep.flow_id == fid).order_by(RepairFlowStep.step_order)
    )
    steps = result.scalars().all()
    return [
        {
            "id": s.id,
            "flow_id": s.flow_id,
            "step_order": s.step_order,
            "step_name": s.step_name,
            "action_role": s.action_role,
            "action_label": s.action_label,
        }
        for s in steps
    ]


@router.post("/{fid}/steps")
async def create_step(
    fid: int,
    req: StepReq,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_role("admin")),
):
    f = await db.get(RepairFlow, fid)
    if not f:
        raise HTTPException(404, "流程不存在")
    if req.action_role not in ("admin", "fleet_manager", "repair_shop", "driver", ""):
        raise HTTPException(400, "无效的角色")
    s = RepairFlowStep(
        flow_id=fid,
        step_order=req.step_order,
        step_name=req.step_name,
        action_role=req.action_role,
        action_label=req.action_label,
    )
    db.add(s)
    await db.commit()
    await db.refresh(s)
    await log_operation(db, user, f"为流程 #{fid} 添加了步骤「{s.step_name}」", "repair_flow_step", s.id)
    return {"id": s.id, "step_order": s.step_order}


@router.put("/steps/{sid}")
async def update_step(
    sid: int,
    req: StepReq,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_role("admin")),
):
    s = await db.get(RepairFlowStep, sid)
    if not s:
        raise HTTPException(404, "步骤不存在")
    if req.action_role not in ("admin", "fleet_manager", "repair_shop", "driver", ""):
        raise HTTPException(400, "无效的角色")
    s.step_order = req.step_order
    s.step_name = req.step_name
    s.action_role = req.action_role
    s.action_label = req.action_label
    await db.commit()
    await log_operation(db, user, f"编辑了步骤「{s.step_name}」", "repair_flow_step", sid)
    return {"msg": "已更新"}


@router.delete("/steps/{sid}")
async def delete_step(
    sid: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_role("admin")),
):
    s = await db.get(RepairFlowStep, sid)
    if not s:
        raise HTTPException(404, "步骤不存在")
    await log_operation(db, user, f"删除了步骤「{s.step_name}」", "repair_flow_step", sid)
    await db.delete(s)
    await db.commit()
    return {"msg": "已删除"}
