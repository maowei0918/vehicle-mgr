"""操作日志 - 只读查看"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc
from database import get_db
from models.operation_log import OperationLog
from models.user import User
from services.auth import get_current_user

router = APIRouter(prefix="/api/logs", tags=["logs"])


@router.get("")
async def list_logs(
    page: int = Query(1, ge=1),
    size: int = Query(50, ge=1, le=200),
    target_type: str | None = Query(None, description="筛选类型"),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """获取操作日志列表（仅管理员可查看全部）"""
    if user.role != "admin":
        # 非管理员只能看自己的日志
        base = select(OperationLog).where(OperationLog.username == user.username)
        count_q = select(func.count()).where(OperationLog.username == user.username)
    else:
        base = select(OperationLog)
        count_q = select(func.count()).select_from(OperationLog)

    if target_type:
        base = base.where(OperationLog.target_type == target_type)
        count_q = count_q.where(OperationLog.target_type == target_type)

    total_r = await db.execute(count_q)
    total = total_r.scalar() or 0

    offset = (page - 1) * size
    rs = await db.execute(
        base.order_by(desc(OperationLog.created_at)).offset(offset).limit(size)
    )
    logs = rs.scalars().all()

    return {
        "items": [
            {
                "id": log.id,
                "username": log.username,
                "user_name": log.user_name,
                "action": log.action,
                "target_type": log.target_type,
                "target_id": log.target_id,
                "created_at": log.created_at.isoformat() if log.created_at else None,
            }
            for log in logs
        ],
        "total": total,
        "page": page,
        "size": size,
    }
