"""认证接口"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel
from database import get_db
from models.user import User
from models.role import RolePermission
from services.auth import hash_password, verify_password, create_token, get_current_user
from services.operation_log import log_operation

router = APIRouter(prefix="/api/auth", tags=["认证"])


class LoginReq(BaseModel):
    username: str
    password: str


class LoginResp(BaseModel):
    token: str
    user: dict


def _build_user_dict(user: User) -> dict:
    """构建用户信息字典"""
    return {
        "id": user.id, "username": user.username, "name": user.name,
        "role": user.role, "phone": user.phone, "group_id": user.group_id,
        "role_id": user.role_id,
    }


async def _get_permissions(db: AsyncSession, user: User) -> list[str]:
    """获取用户权限列表"""
    if user.role == "admin":
        # 管理员拥有全部权限——直接从 permission 常量返回
        from services.permissions import ALL_PERMISSIONS
        return [p["key"] for p in ALL_PERMISSIONS]
    if not user.role_id:
        return []
    result = await db.execute(
        select(RolePermission.permission_key).where(RolePermission.role_id == user.role_id)
    )
    return [r[0] for r in result.all()]


@router.post("/login")
async def login(req: LoginReq, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.username == req.username, User.is_active == True))
    user = result.scalar_one_or_none()
    if not user or not verify_password(req.password, user.password_hash):
        raise HTTPException(status_code=401, detail="用户名或密码错误")
    token = create_token(user.id, user.role)
    await log_operation(db, user, f"登录了系统")
    ud = _build_user_dict(user)
    ud["permissions"] = await _get_permissions(db, user)
    return LoginResp(token=token, user=ud)


@router.get("/me")
async def get_me(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    ud = _build_user_dict(user)
    ud["permissions"] = await _get_permissions(db, user)
    return ud


@router.post("/init")
async def init_admin(db: AsyncSession = Depends(get_db)):
    """首次初始化管理员账号"""
    result = await db.execute(select(User).where(User.role == "admin"))
    if result.first():
        raise HTTPException(status_code=400, detail="管理员已存在")
    admin = User(
        username="admin", password_hash=hash_password("admin123"),
        name="管理员", role="admin", is_active=True
    )
    db.add(admin)
    await db.commit()
    return {"msg": "管理员已创建（admin / admin123）"}
