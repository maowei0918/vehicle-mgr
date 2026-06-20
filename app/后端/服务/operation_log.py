"""操作日志工具"""
from models.operation_log import OperationLog
from models.user import User
from sqlalchemy.ext.asyncio import AsyncSession


async def log_operation(
    db: AsyncSession,
    user: User,
    action: str,
    target_type: str = "",
    target_id: int | None = None,
):
    """写入一条操作日志
    
    Args:
        db: 数据库会话
        user: 当前操作用户
        action: 操作描述（中文），如"创建了用户「张三」"
        target_type: 对象类型，如 "user" / "vehicle" / "repair"
        target_id: 对象ID
    """
    log = OperationLog(
        username=user.username,
        user_name=user.name or user.username,
        action=action,
        target_type=target_type,
        target_id=target_id,
    )
    db.add(log)
    # 不 commit，由调用方统一 commit
