"""网页设置页 — 浏览器修改配置"""
import os
from pathlib import Path
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel
from models.user import User
from services.auth import get_current_user, require_role
from services.operation_log import log_operation
from database import get_db

router = APIRouter(prefix="/api/settings", tags=["设置"])

BASE_DIR = Path(__file__).resolve().parent.parent
ENV_FILE = BASE_DIR / ".env"

SETTING_KEYS = {
    "SITE_TITLE": "网站标题",
    "DATA_DIR": "数据存储目录",
    "PORT": "服务端口",
    "OCR_ENABLED": "OCR 里程识别",
    "MILEAGE_THRESHOLD": "里程预警阈值(km)",
    "DB_DIR": "数据库目录",
    "UPLOAD_DIR": "照片目录",
    "BACKUP_DIR": "备份目录",
    "BACKUP_INTERVAL_HOURS": "自动备份间隔(小时)",
    "BACKUP_RETENTION": "自动备份保留数量",
    "REGULAR_BACKUP_ENABLED": "增量备份启用",
    "REGULAR_BACKUP_INTERVAL_HOURS": "增量备份间隔(小时)",
    "REGULAR_BACKUP_DAYS": "增量备份天数",
}

class SiteTitleResp(BaseModel):
    title: str


@router.get("/site-title", response_model=SiteTitleResp)
async def get_site_title():
    """获取网站标题（公开接口，无需登录）"""
    title = os.getenv("SITE_TITLE", "车辆管理系统")
    # 从 .env 文件读取
    if ENV_FILE.exists():
        with open(ENV_FILE, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line.startswith("SITE_TITLE="):
                    title = line.split("=", 1)[1].strip()
                    break
    return SiteTitleResp(title=title)


class SettingsResp(BaseModel):
    settings: dict
    env_file_path: str


class SettingsUpdate(BaseModel):
    key: str
    value: str


@router.get("")
async def get_settings(user: User = Depends(require_role("admin"))):
    """读取当前配置"""
    result = {}
    for key in SETTING_KEYS:
        result[key] = os.getenv(key, "")

    # 从 .env 文件读取（如果存在）
    if ENV_FILE.exists():
        with open(ENV_FILE, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    k, v = line.split("=", 1)
                    if k in SETTING_KEYS:
                        result[k] = v

    # 补充实际值
    try:
        from config import UPLOAD_DIR, PORT, MILEAGE_THRESHOLD, OCR_ENABLED
        if not result.get("UPLOAD_DIR"): result["UPLOAD_DIR"] = str(UPLOAD_DIR)
        if not result.get("PORT"): result["PORT"] = str(PORT)
        if not result.get("MILEAGE_THRESHOLD"): result["MILEAGE_THRESHOLD"] = str(MILEAGE_THRESHOLD)
        if not result.get("OCR_ENABLED"): result["OCR_ENABLED"] = str(OCR_ENABLED).lower()
    except ImportError:
        pass

    return SettingsResp(settings=result, env_file_path=str(ENV_FILE))


@router.put("")
async def update_setting(
    req: SettingsUpdate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_role("admin")),
):
    """修改单个配置项"""
    if req.key not in SETTING_KEYS:
        raise HTTPException(400, f"不支持的配置项: {req.key}")

    # 读取或创建 .env
    lines = []
    if ENV_FILE.exists():
        lines = ENV_FILE.read_text(encoding="utf-8").splitlines()

    updated = False
    new_lines = []
    for line in lines:
        if line.strip().startswith(f"{req.key}="):
            new_lines.append(f"{req.key}={req.value}")
            updated = True
        else:
            new_lines.append(line)

    if not updated:
        new_lines.append(f"{req.key}={req.value}")

    ENV_FILE.write_text("\n".join(new_lines) + "\n", encoding="utf-8")
    await log_operation(db, user, f"修改了系统设置「{SETTING_KEYS.get(req.key, req.key)}」为 {req.value}", "settings")
    return {"msg": f"已更新 {SETTING_KEYS[req.key]}", "key": req.key, "value": req.value}
