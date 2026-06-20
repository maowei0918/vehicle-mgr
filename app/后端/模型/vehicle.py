"""车辆模型"""
import datetime
from sqlalchemy import String, Integer, DateTime, ForeignKey, Boolean, Text, Date, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from database import Base


class Vehicle(Base):
    __tablename__ = "vehicles"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    plate_number: Mapped[str] = mapped_column(String(20), unique=True, nullable=False, index=True)
    brand: Mapped[str] = mapped_column(String(64), default="")
    model: Mapped[str] = mapped_column(String(64), default="")
    color: Mapped[str] = mapped_column(String(20), default="")
    vin: Mapped[str] = mapped_column(String(64), default="")
    registration_date: Mapped[datetime.date | None] = mapped_column(Date, nullable=True)
    group_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("groups.id"), nullable=True)
    # 当前驾驶员/责任人
    driver_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("users.id"), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    notes: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime.datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())

    group = relationship("Group", back_populates="vehicles", lazy="selectin")
    driver = relationship("User", lazy="selectin")
