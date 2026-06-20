"""日检模型"""
import datetime
from sqlalchemy import String, Integer, Float, DateTime, ForeignKey, Text, JSON, func
from sqlalchemy.orm import Mapped, mapped_column
from database import Base


class Inspection(Base):
    __tablename__ = "inspections"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    vehicle_id: Mapped[int] = mapped_column(Integer, ForeignKey("vehicles.id"), nullable=False, index=True)
    driver_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False)
    # 检查日期
    inspection_date: Mapped[str] = mapped_column(String(10), nullable=False)  # YYYY-MM-DD

    # 拍照 JSON: [{url, desc}]
    exterior_photos: Mapped[str] = mapped_column(Text, default="[]")  # JSON
    cabin_photos: Mapped[str] = mapped_column(Text, default="[]")     # JSON
    odometer_photo: Mapped[str] = mapped_column(Text, default="")     # 里程表照片URL

    # 里程数据
    odometer_reading: Mapped[int | None] = mapped_column(Integer, nullable=True)   # AI识别或手动输入的公里数
    last_odometer: Mapped[int | None] = mapped_column(Integer, nullable=True)      # 上次里程
    mileage_diff: Mapped[int | None] = mapped_column(Integer, nullable=True)        # 差值
    threshold_exceeded: Mapped[bool | None] = mapped_column(Integer, nullable=True) # 是否超阈值

    # 异常/备注
    issues: Mapped[str] = mapped_column(Text, default="")
    status: Mapped[str] = mapped_column(String(20), default="pending")  # pending / verified
    verified_by: Mapped[int | None] = mapped_column(Integer, ForeignKey("users.id"), nullable=True)
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime, server_default=func.now())
