"""角色 & 角色权限模型"""
import datetime
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Boolean, Text, func
from sqlalchemy.orm import relationship
from database import Base


class Role(Base):
    __tablename__ = "roles"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(64), unique=True, nullable=False, comment="角色名标识 admin/fleet_manager/repair_shop/driver")
    display_name = Column(String(64), default="", comment="显示名称如「管理员」「车管员」")
    desc = Column(Text, default="", comment="描述")
    data_scope = Column(String(16), default="all", comment="数据范围: all=全部, group=本组, self=自己/指派")
    is_system = Column(Boolean, default=False, comment="系统角色不可删除")
    created_at = Column(DateTime, server_default=func.now())

    permissions = relationship("RolePermission", back_populates="role", lazy="selectin", cascade="all, delete-orphan")


class RolePermission(Base):
    __tablename__ = "role_permissions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    role_id = Column(Integer, ForeignKey("roles.id", ondelete="CASCADE"), nullable=False)
    permission_key = Column(String(64), nullable=False, comment="权限标识")

    role = relationship("Role", back_populates="permissions")
