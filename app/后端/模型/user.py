"""用户 & 分组模型"""
import datetime
from sqlalchemy import String, Boolean, Integer, DateTime, ForeignKey, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from database import Base


class Group(Base):
    __tablename__ = "groups"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    desc: Mapped[str] = mapped_column(String(256), default="")
    parent_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("groups.id"), nullable=True, default=None)
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime, server_default=func.now())

    # 递归关联：上级分组 & 子分组
    parent = relationship("Group", remote_side="Group.id", back_populates="children", lazy="selectin")
    children = relationship("Group", back_populates="parent", lazy="selectin")

    users = relationship("User", back_populates="group", lazy="selectin")
    vehicles = relationship("Vehicle", back_populates="group", lazy="selectin")


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    username: Mapped[str] = mapped_column(String(64), unique=True, nullable=False, index=True)
    password_hash: Mapped[str] = mapped_column(String(256), nullable=False)
    name: Mapped[str] = mapped_column(String(64), nullable=False)
    phone: Mapped[str] = mapped_column(String(20), default="")
    # 角色: admin / fleet_manager / repair_shop / driver（旧字段，用于快速判断）
    role: Mapped[str] = mapped_column(String(20), nullable=False, default="driver")
    # 新角色系统：指向 roles 表（可空，迁移兼容）
    role_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("roles.id"), nullable=True)
    # 车管员和司机属于某个分组；admin 和 汽修厂 可以跨组
    group_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("groups.id"), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime, server_default=func.now())

    group = relationship("Group", back_populates="users", lazy="selectin")
    role_obj = relationship("Role", lazy="selectin")
