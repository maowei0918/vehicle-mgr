"""操作日志模型"""
from sqlalchemy import Column, Integer, String, DateTime, Text
from database import Base
import datetime


class OperationLog(Base):
    __tablename__ = "operation_logs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(64), default="", comment="操作用户名")
    user_name = Column(String(64), default="", comment="用户姓名/中文")
    action = Column(Text, default="", comment="操作内容")
    target_type = Column(String(32), default="", comment="操作对象类型")
    target_id = Column(Integer, nullable=True, comment="操作对象ID")
    created_at = Column(DateTime, default=datetime.datetime.now)
