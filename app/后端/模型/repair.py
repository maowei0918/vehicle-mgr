"""维修模型"""
import datetime
from sqlalchemy import String, Integer, Float, DateTime, ForeignKey, Text, JSON, func, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship
from database import Base


class RepairOrder(Base):
    """维修工单"""
    __tablename__ = "repair_orders"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    vehicle_id: Mapped[int] = mapped_column(Integer, ForeignKey("vehicles.id"), nullable=False, index=True)
    # 车管员派单
    created_by: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False)
    # 指派给汽修厂 (user id)
    assigned_to: Mapped[int | None] = mapped_column(Integer, ForeignKey("users.id"), nullable=True)
    # 汽修厂名称
    shop_name: Mapped[str] = mapped_column(String(128), default="")

    # 故障描述
    description: Mapped[str] = mapped_column(Text, default="")
    # 接单/派单照片 JSON
    dispatch_photos: Mapped[str] = mapped_column(Text, default="[]")
    accept_photos: Mapped[str] = mapped_column(Text, default="[]")
    # 车管员验收照片
    verify_photos: Mapped[str] = mapped_column(Text, default="[]")

    # 状态: dispatched / accepted / in_progress / completed / verified / rejected
    status: Mapped[str] = mapped_column(String(20), default="dispatched")
    # 自定义流程支持
    flow_id: Mapped[int | None] = mapped_column(Integer, nullable=True, comment="关联流程ID")
    current_step: Mapped[int] = mapped_column(Integer, default=0, comment="当前步骤序号，0=待派单")
    # 验收备注
    verify_notes: Mapped[str] = mapped_column(Text, default="")

    created_at: Mapped[datetime.datetime] = mapped_column(DateTime, server_default=func.now())
    accepted_at: Mapped[datetime.datetime | None] = mapped_column(DateTime, nullable=True)
    completed_at: Mapped[datetime.datetime | None] = mapped_column(DateTime, nullable=True)
    verified_at: Mapped[datetime.datetime | None] = mapped_column(DateTime, nullable=True)

    details = relationship("RepairDetail", back_populates="order", lazy="selectin",
                           cascade="all, delete-orphan")


class RepairDetail(Base):
    """维修明细"""
    __tablename__ = "repair_details"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    order_id: Mapped[int] = mapped_column(Integer, ForeignKey("repair_orders.id"), nullable=False)
    # 维修项目
    item_name: Mapped[str] = mapped_column(String(128), nullable=False)
    item_desc: Mapped[str] = mapped_column(Text, default="")
    # 更换零件
    parts_used: Mapped[str] = mapped_column(Text, default="")
    # 费用
    cost: Mapped[float] = mapped_column(Float, default=0)
    # 质保期
    warranty_days: Mapped[int] = mapped_column(Integer, default=0)
    warranty_end: Mapped[str | None] = mapped_column(String(10), nullable=True)  # YYYY-MM-DD
    # 维修照片(这一步不需要)
    photos: Mapped[str] = mapped_column(Text, default="[]")

    created_at: Mapped[datetime.datetime] = mapped_column(DateTime, server_default=func.now())

    order = relationship("RepairOrder", back_populates="details", lazy="selectin")


class WarrantyAlert(Base):
    """质保期内再次维修提醒"""
    __tablename__ = "warranty_alerts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    detail_id: Mapped[int] = mapped_column(Integer, ForeignKey("repair_details.id"), nullable=False)
    vehicle_id: Mapped[int] = mapped_column(Integer, ForeignKey("vehicles.id"), nullable=False)
    # 原维修明细
    original_item: Mapped[str] = mapped_column(String(128), default="")
    warranty_end: Mapped[str] = mapped_column(String(10), default="")
    # 新维修单ID(再次维修)
    new_order_id: Mapped[int] = mapped_column(Integer, ForeignKey("repair_orders.id"), nullable=False)
    is_read: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime, server_default=func.now())
