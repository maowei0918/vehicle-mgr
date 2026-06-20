"""角色管理 API"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from pydantic import BaseModel
from database import get_db
from models.role import Role, RolePermission
from models.user import User
from services.auth import get_current_user, require_role
from services.permissions import ALL_PERMISSIONS, PERMISSIONS_BY_MODULE

router = APIRouter(prefix="/api/roles", tags=["角色管理"])


class RoleReq(BaseModel):
    name: str = ""
    display_name: str = ""
    desc: str = ""
    data_scope: str = "all"


@router.get("")
async def list_roles(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_role("admin")),
):
    """角色列表（含权限）"""
    result = await db.execute(select(Role).order_by(desc(Role.id)))
    roles = result.scalars().all()
    return [
        {
            "id": r.id,
            "name": r.name,
            "display_name": r.display_name,
            "desc": r.desc,
            "is_system": r.is_system,
            "data_scope": r.data_scope,
            "permissions": [p.permission_key for p in r.permissions],
        }
        for r in roles
    ]


@router.get("/simple")
async def list_roles_simple(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """角色精简列表（给前端下拉用）"""
    result = await db.execute(select(Role).order_by(Role.id))
    roles = result.scalars().all()
    return [
        {"id": r.id, "name": r.name, "display_name": r.display_name, "data_scope": r.data_scope}
        for r in roles
    ]


@router.post("")
async def create_role(
    req: RoleReq,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_role("admin")),
):
    """新建角色"""
    if not req.name.strip():
        raise HTTPException(400, "角色名不能为空")
    exist = await db.execute(select(Role).where(Role.name == req.name.strip()))
    if exist.scalar_one_or_none():
        raise HTTPException(400, "角色名已存在")
    r = Role(name=req.name.strip(), display_name=req.display_name.strip(), desc=req.desc.strip(), data_scope=req.data_scope if req.data_scope in ("all","group","self") else "all")
    db.add(r)
    await db.commit()
    await db.refresh(r)
    return {"id": r.id, "name": r.name, "display_name": r.display_name, "data_scope": r.data_scope}


@router.put("/{rid}")
async def update_role(
    rid: int,
    req: RoleReq,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_role("admin")),
):
    """编辑角色"""
    r = await db.get(Role, rid)
    if not r:
        raise HTTPException(404, "角色不存在")
    if req.name.strip():
        r.name = req.name.strip()
    if req.display_name:
        r.display_name = req.display_name.strip()
    if req.desc:
        r.desc = req.desc.strip()
    if req.data_scope in ("all", "group", "self"):
        r.data_scope = req.data_scope
    await db.commit()
    return {"msg": "已更新"}


@router.delete("/{rid}")
async def delete_role(
    rid: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_role("admin")),
):
    """删除角色（系统角色不可删除）"""
    r = await db.get(Role, rid)
    if not r:
        raise HTTPException(404, "角色不存在")
    if r.is_system:
        raise HTTPException(400, "系统角色不可删除")
    # 检查是否有用户使用此角色
    users_r = await db.execute(select(User).where(User.role_id == rid).limit(1))
    if users_r.scalar_one_or_none():
        raise HTTPException(400, "该角色下还有用户，无法删除")
    await db.delete(r)
    await db.commit()
    return {"msg": "已删除"}


# ====== 角色权限分配 ======

@router.get("/{rid}/permissions")
async def get_role_permissions(
    rid: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_role("admin")),
):
    """获取角色已分配的权限"""
    r = await db.get(Role, rid)
    if not r:
        raise HTTPException(404, "角色不存在")
    return {
        "role_id": rid,
        "permissions": [p.permission_key for p in r.permissions],
    }


@router.put("/{rid}/permissions")
async def set_role_permissions(
    rid: int,
    body: dict,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_role("admin")),
):
    """设置角色权限（全量覆盖）"""
    r = await db.get(Role, rid)
    if not r:
        raise HTTPException(404, "角色不存在")
    permission_keys = body.get("permissions", [])
    # 校验权限 key 是否合法
    valid_keys = {p["key"] for p in ALL_PERMISSIONS}
    for k in permission_keys:
        if k not in valid_keys:
            raise HTTPException(400, f"无效的权限: {k}")
    # 删除旧权限
    for old in r.permissions:
        await db.delete(old)
    # 写入新权限
    for key in permission_keys:
        db.add(RolePermission(role_id=rid, permission_key=key))
    await db.commit()
    return {"msg": "权限已更新", "permissions": permission_keys}


# ====== 获取所有权限点定义（给前端用） ======

@router.get("/definitions")
async def get_permission_definitions():
    """返回所有权限点定义"""
    return PERMISSIONS_BY_MODULE
