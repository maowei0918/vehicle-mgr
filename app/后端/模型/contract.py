"""合同模型（合同头）"""
from datetime import datetime
from sqlalchemy import String, Boolean, Integer, Text, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column
from database import Base


class Contract(Base):
    __tablename__ = "contracts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(128), default="", comment="合同名称")
    notes: Mapped[str] = mapped_column(Text, default="", comment="合同备注")
    is_active: Mapped[bool] = mapped_column(Boolean, default=False, comment="是否启用（同一时间只能启用一份）")
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
