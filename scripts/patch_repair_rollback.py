from pathlib import Path
base=Path('/vol1/@appcenter/vehicle-mgr/后端')

# model: add rollback_reason
p=base/'模型/repair.py'
s=p.read_text(encoding='utf-8')
if 'rollback_reason' not in s:
    s=s.replace(
'''    verify_notes: Mapped[str | None] = mapped_column(Text, nullable=True)''',
'''    verify_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    rollback_reason: Mapped[str] = mapped_column(Text, default="")'''
    )
p.write_text(s,encoding='utf-8')

# db migration
p=base/'database.py'
s=p.read_text(encoding='utf-8')
if 'rollback_reason' not in s:
    # add after the last existing migration block
    old='''        try:
            await conn.exec_driver_sql("ALTER TABLE contract_parts ADD COLUMN total_amount FLOAT DEFAULT 0")
        except Exception:
            pass'''
    new=old+'''
        try:
            await conn.exec_driver_sql("ALTER TABLE repair_orders ADD COLUMN rollback_reason TEXT DEFAULT ''")
        except Exception:
            pass'''
    s=s.replace(old,new)
p.write_text(s,encoding='utf-8')

# router: add rollback/cancel endpoints
p=base/'路由/repair.py'
s=p.read_text(encoding='utf-8')

old='''@router.put("/{oid}/complete")'''
new='''class RollbackReq(BaseModel):
    reason: str = ""

@router.put("/{oid}/cancel")
async def cancel_repair(oid: int, req: RollbackReq, db: AsyncSession = Depends(get_db),
                        user: User = Depends(require_role("fleet_manager", "admin"))):
    """车管员撤回已派单（dispatched → cancelled）"""
    order = await db.get(RepairOrder, oid)
    if not order:
        raise HTTPException(404, "维修单不存在")
    if order.status != "dispatched":
        raise HTTPException(400, "只有已派单状态可撤回")
    await ensure_repair_access(db, user, order)
    order.status = "cancelled"
    order.rollback_reason = req.reason
    await db.commit()
    return {"msg": "已撤回", "status": "cancelled"}

@router.put("/{oid}/reject")
async def reject_repair(oid: int, req: RollbackReq, db: AsyncSession = Depends(get_db),
                        user: User = Depends(require_role("repair_shop"))):
    """汽修厂退回（accepted → dispatched，退回给车管员重新派）"""
    order = await db.get(RepairOrder, oid)
    if not order:
        raise HTTPException(404, "维修单不存在")
    if order.status != "accepted":
        raise HTTPException(400, "只有已接单状态可退回")
    if order.assigned_to and order.assigned_to != user.id:
        raise HTTPException(403, "该维修单未指派给当前修理厂")
    order.status = "dispatched"
    order.rollback_reason = req.reason
    await db.commit()
    return {"msg": "已退回", "status": "dispatched"}

@router.put("/{oid}/withdraw-details")
async def withdraw_details(oid: int, req: RollbackReq, db: AsyncSession = Depends(get_db),
                           user: User = Depends(require_role("repair_shop"))):
    """汽修厂撤回明细（submitted → accepted，清除明细，重新填）"""
    order = await db.get(RepairOrder, oid)
    if not order:
        raise HTTPException(404, "维修单不存在")
    if order.status != "submitted":
        raise HTTPException(400, "只有已提交明细状态可撤回")
    if order.assigned_to and order.assigned_to != user.id:
        raise HTTPException(403, "该维修单未指派给当前修理厂")
    # 删除明细
    for d in order.details:
        await db.delete(d)
    order.status = "accepted"
    order.rollback_reason = req.reason
    await db.commit()
    return {"msg": "明细已撤回", "status": "accepted"}

@router.put("/{oid}/send-back")
async def send_back_repair(oid: int, req: RollbackReq, db: AsyncSession = Depends(get_db),
                           user: User = Depends(require_role("fleet_manager", "admin"))):
    """车管员退回维修单（completed → submitted，让修理厂重做）"""
    order = await db.get(RepairOrder, oid)
    if not order:
        raise HTTPException(404, "维修单不存在")
    if order.status != "completed":
        raise HTTPException(400, "只有已完成状态可退回")
    await ensure_repair_access(db, user, order)
    order.status = "submitted"
    order.rollback_reason = req.reason
    await db.commit()
    return {"msg": "已退回给修理厂", "status": "submitted"}

@router.put("/{oid}/re-verify")
async def reverify_repair(oid: int, req: RollbackReq, db: AsyncSession = Depends(get_db),
                          user: User = Depends(require_role("fleet_manager", "admin"))):
    """车管员撤回验收（verified → completed，重新验收）"""
    order = await db.get(RepairOrder, oid)
    if not order:
        raise HTTPException(404, "维修单不存在")
    if order.status != "verified":
        raise HTTPException(400, "只有已验收状态可撤回验收")
    await ensure_repair_access(db, user, order)
    order.status = "completed"
    order.rollback_reason = req.reason
    order.verify_photos = "[]"
    order.verify_notes = ""
    await db.commit()
    return {"msg": "已撤回验收", "status": "completed"}

@router.put("/{oid}/complete")'''
if old in s:
    s=s.replace(old,new)
else:
    print('WARN complete endpoint not matched')

# add rollback_reason to detail response
s=s.replace(
'''"verify_notes": order.verify_notes,''',
'''"verify_notes": order.verify_notes,
        "rollback_reason": order.rollback_reason,''')

# add rollback_reason to list response
s=s.replace(
'''"status": o.status,
            "created_at": o.created_at.isoformat() if o.created_at else None,''',
'''"status": o.status,
            "rollback_reason": o.rollback_reason,
            "created_at": o.created_at.isoformat() if o.created_at else None,''')
p.write_text(s,encoding='utf-8')
print('repair rollback endpoints patched')
