"""权限点定义 & 校验 & 数据范围过滤"""
import logging
from typing import Type, Any, List
from sqlalchemy import select
from sqlalchemy.sql import Select
from fastapi import Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from database import get_db
from models.user import User, Group
from models.role import Role, RolePermission
from models.vehicle import Vehicle
from models.inspection import Inspection
from models.repair import RepairOrder
from services.auth import get_current_user

logger = logging.getLogger(__name__)


async def get_descendant_group_ids(db: AsyncSession, group_id: int) -> List[int]:
    """递归获取所有子分组 ID（含自身），支持多级层级
    
    用于数据范围"本组"时，过滤出本组及所有下级分组的数据。
    """
    ids = [group_id]
    queue = [group_id]
    while queue:
        pid = queue.pop(0)
        result = await db.execute(select(Group.id).where(Group.parent_id == pid))
        child_ids = [r[0] for r in result]
        ids.extend(child_ids)
        queue.extend(child_ids)
    return ids


# ===== 权限点常量 =====
USER_VIEW = "user.view"
USER_CREATE = "user.create"
USER_EDIT = "user.edit"
USER_DELETE = "user.delete"
USER_IMPORT = "user.import"
GROUP_VIEW = "group.view"
GROUP_CREATE = "group.create"
GROUP_DELETE = "group.delete"
VEHICLE_VIEW = "vehicle.view"
VEHICLE_CREATE = "vehicle.create"
VEHICLE_EDIT = "vehicle.edit"
VEHICLE_DELETE = "vehicle.delete"
VEHICLE_IMPORT = "vehicle.import"
VEHICLE_EXPORT = "vehicle.export"
INSPECTION_VIEW = "inspection.view"
INSPECTION_CREATE = "inspection.create"
INSPECTION_REPORT = "inspection.report"
REPAIR_VIEW = "repair.view"
REPAIR_DISPATCH = "repair.dispatch"
REPAIR_ACCEPT = "repair.accept"
REPAIR_DETAIL = "repair.detail_upload"
REPAIR_COMPLETE = "repair.complete"
REPAIR_VERIFY = "repair.verify"
REPAIR_EXPORT = "repair.export"
REPAIR_ADVANCE = "repair.advance_step"
CONTRACT_VIEW = "contract.view"
CONTRACT_CREATE = "contract.create"
CONTRACT_EDIT = "contract.edit"
CONTRACT_DELETE = "contract.delete"
CONTRACT_ACTIVATE = "contract.activate"
PART_VIEW = "contract_part.view"
PART_CREATE = "contract_part.create"
PART_EDIT = "contract_part.edit"
PART_DELETE = "contract_part.delete"
PART_IMPORT = "contract_part.import"
FLOW_VIEW = "repair_flow.view"
FLOW_CREATE = "repair_flow.create"
FLOW_EDIT = "repair_flow.edit"
FLOW_DELETE = "repair_flow.delete"
SETTINGS_EDIT = "settings.edit"
LOG_VIEW = "log.view"

ALL_PERMISSIONS = [
    {"key": USER_VIEW, "module": "用户管理", "name": "查看用户"},
    {"key": USER_CREATE, "module": "用户管理", "name": "创建用户"},
    {"key": USER_EDIT, "module": "用户管理", "name": "编辑用户"},
    {"key": USER_DELETE, "module": "用户管理", "name": "删除用户"},
    {"key": USER_IMPORT, "module": "用户管理", "name": "导入用户"},
    {"key": GROUP_VIEW, "module": "分组管理", "name": "查看分组"},
    {"key": GROUP_CREATE, "module": "分组管理", "name": "创建分组"},
    {"key": GROUP_DELETE, "module": "分组管理", "name": "删除分组"},
    {"key": VEHICLE_VIEW, "module": "车辆管理", "name": "查看车辆"},
    {"key": VEHICLE_CREATE, "module": "车辆管理", "name": "添加车辆"},
    {"key": VEHICLE_EDIT, "module": "车辆管理", "name": "编辑车辆"},
    {"key": VEHICLE_DELETE, "module": "车辆管理", "name": "删除车辆"},
    {"key": VEHICLE_IMPORT, "module": "车辆管理", "name": "导入车辆"},
    {"key": VEHICLE_EXPORT, "module": "车辆管理", "name": "导出车辆"},
    {"key": INSPECTION_VIEW, "module": "日检管理", "name": "查看日检"},
    {"key": INSPECTION_REPORT, "module": "车辆日检", "name": "车辆日检"},
    {"key": REPAIR_VIEW, "module": "维修管理", "name": "查看维修单"},
    {"key": REPAIR_DISPATCH, "module": "维修管理", "name": "派单"},
    {"key": REPAIR_ACCEPT, "module": "维修管理", "name": "接单"},
    {"key": REPAIR_DETAIL, "module": "维修管理", "name": "上传明细"},
    {"key": REPAIR_COMPLETE, "module": "维修管理", "name": "完成维修"},
    {"key": REPAIR_VERIFY, "module": "维修管理", "name": "验收"},
    {"key": REPAIR_EXPORT, "module": "维修管理", "name": "导出"},
    {"key": REPAIR_ADVANCE, "module": "维修管理", "name": "推进流程"},
    {"key": CONTRACT_VIEW, "module": "合同管理", "name": "查看合同"},
    {"key": CONTRACT_CREATE, "module": "合同管理", "name": "创建合同"},
    {"key": CONTRACT_EDIT, "module": "合同管理", "name": "编辑合同"},
    {"key": CONTRACT_DELETE, "module": "合同管理", "name": "删除合同"},
    {"key": CONTRACT_ACTIVATE, "module": "合同管理", "name": "启用合同"},
    {"key": PART_VIEW, "module": "合同配件", "name": "查看配件"},
    {"key": PART_CREATE, "module": "合同配件", "name": "添加配件"},
    {"key": PART_EDIT, "module": "合同配件", "name": "编辑配件"},
    {"key": PART_DELETE, "module": "合同配件", "name": "删除配件"},
    {"key": PART_IMPORT, "module": "合同配件", "name": "导入配件"},
    {"key": FLOW_VIEW, "module": "维修流程", "name": "查看流程"},
    {"key": FLOW_CREATE, "module": "维修流程", "name": "创建流程"},
    {"key": FLOW_EDIT, "module": "维修流程", "name": "编辑流程"},
    {"key": FLOW_DELETE, "module": "维修流程", "name": "删除流程"},
    {"key": SETTINGS_EDIT, "module": "系统设置", "name": "修改配置"},
    {"key": LOG_VIEW, "module": "操作日志", "name": "查看日志"},
]

PERMISSIONS_BY_MODULE = {}
for p in ALL_PERMISSIONS:
    PERMISSIONS_BY_MODULE.setdefault(p["module"], []).append(p)


async def scope_query(query: Select, user: User, model_class: Type[Any], db: AsyncSession | None = None) -> Select:
    """根据用户角色的数据范围，给查询加上过滤条件
    
    适用模型：Vehicle, Inspection, RepairOrder, User
    - all: 全部数据
    - group: 本组及所有下级分组数据（递归，需要 db 参数）
    - self: 自己的/指派给自己的
    """
    if user.role == "admin":
        return query  # admin 永远看全部

    data_scope = "all"
    if user.role_id and user.role_obj:
        data_scope = user.role_obj.data_scope or "all"
    else:
        data_scope_map = {"admin": "all", "fleet_manager": "group", "repair_shop": "self", "driver": "self"}
        data_scope = data_scope_map.get(user.role, "all")

    if data_scope == "all":
        return query

    if data_scope == "group" and user.group_id:
        # 支持递归分组：获取本组及所有子分组 ID
        if db is not None:
            gids = await get_descendant_group_ids(db, user.group_id)
        else:
            gids = [user.group_id]
        if model_class is Vehicle:
            return query.where(Vehicle.group_id.in_(gids))
        if model_class is User or model_class.__name__ == "User":
            return query.where(User.group_id.in_(gids))
        if model_class is Inspection:
            return query.join(Vehicle, Inspection.vehicle_id == Vehicle.id).where(Vehicle.group_id.in_(gids))
        if model_class is RepairOrder:
            return query.join(Vehicle, RepairOrder.vehicle_id == Vehicle.id).where(Vehicle.group_id.in_(gids))
    if data_scope == "self":
        if model_class is Vehicle:
            return query.where(Vehicle.driver_id == user.id)
        if model_class is Inspection:
            return query.where(Inspection.driver_id == user.id)
        if model_class is RepairOrder:
            return query.where((RepairOrder.assigned_to == user.id) | (RepairOrder.created_by == user.id))
        if model_class is User or model_class.__name__ == "User":
            return query.where(User.id == user.id)
    return query


async def has_permission(db: AsyncSession, user: User, permission_key: str) -> bool:
    if user.role == "admin":
        return True
    if not user.role_id:
        return _legacy_check(user.role, permission_key)
    result = await db.execute(
        select(RolePermission).where(RolePermission.role_id == user.role_id, RolePermission.permission_key == permission_key)
    )
    return result.scalar_one_or_none() is not None


def _legacy_check(role: str, permission_key: str) -> bool:
    if role == "admin":
        return True
    if role == "fleet_manager":
        return permission_key in [
            USER_VIEW, GROUP_VIEW, VEHICLE_VIEW, VEHICLE_CREATE, VEHICLE_EDIT, VEHICLE_IMPORT, VEHICLE_EXPORT,
            INSPECTION_VIEW, REPAIR_VIEW, REPAIR_DISPATCH, REPAIR_VERIFY, REPAIR_EXPORT, REPAIR_ADVANCE,
            CONTRACT_VIEW, PART_VIEW, FLOW_VIEW, LOG_VIEW,
        ]
    if role == "repair_shop":
        return permission_key in [
            REPAIR_VIEW, REPAIR_ACCEPT, REPAIR_DETAIL, REPAIR_COMPLETE, REPAIR_ADVANCE,
        ]
    if role == "driver":
        return permission_key in [VEHICLE_VIEW, INSPECTION_REPORT]
    return False


async def require_permission(permission_key: str):
    async def checker(db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
        if not await has_permission(db, user, permission_key):
            raise HTTPException(status_code=403, detail="无权限")
        return user
    return checker
