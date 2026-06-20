"""合同配件模型"""
from datetime import datetime
from sqlalchemy import String, Integer, Float, Text, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column
from database import Base


class ContractPart(Base):
    __tablename__ = "contract_parts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    contract_id: Mapped[int | None] = mapped_column(Integer, nullable=True, index=True, comment="关联合同ID")
    shop_id: Mapped[int | None] = mapped_column(Integer, nullable=True, index=True)
    vehicle_model: Mapped[str] = mapped_column(String(128), default="", index=True)
    part_name: Mapped[str] = mapped_column(String(128), nullable=False)
    part_model: Mapped[str] = mapped_column(String(128), default="")
    contract_price: Mapped[float] = mapped_column(Float, default=0.0)
    labor_fee: Mapped[float] = mapped_column(Float, default=0.0)
    total_amount: Mapped[float] = mapped_column(Float, default=0.0)
    warranty_days: Mapped[int] = mapped_column(Integer, default=0)
    notes: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
