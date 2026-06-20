"""维修流程自定义模型"""
from datetime import datetime
from sqlalchemy import String, Integer, Text, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column
from database import Base


class RepairFlow(Base):
    """维修流程定义"""
    __tablename__ = "repair_flows"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(128), default="", comment="流程名称")
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())


class RepairFlowStep(Base):
    """流程步骤"""
    __tablename__ = "repair_flow_steps"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    flow_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True, comment="关联流程ID")
    step_order: Mapped[int] = mapped_column(Integer, default=0, comment="步骤序号，从1开始")
    step_name: Mapped[str] = mapped_column(String(64), default="", comment="步骤名称，如'派单'")
    action_role: Mapped[str] = mapped_column(String(32), default="", comment="操作角色: fleet_manager/repair_shop/admin/driver")
    action_label: Mapped[str] = mapped_column(String(64), default="", comment="操作按钮文字，如'接单'")
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
