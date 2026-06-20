"""车辆管理系统 - 后端配置
所有路径均支持环境变量自定义，无需改代码。
支持 .env 文件（复制 .env.example 为 .env 即可）。
"""
import os
from pathlib import Path

# 加载 .env 文件（如果存在）
try:
    from dotenv import load_dotenv
    env_path = Path(__file__).resolve().parent / ".env"
    if env_path.exists():
        load_dotenv(env_path)
except ImportError:
    pass

BASE_DIR = Path(__file__).resolve().parent

# ---------- 数据存储目录 ----------
# 可设环境变量 DATA_DIR 统一指定数据根目录
DATA_DIR = os.getenv("DATA_DIR", "")

if DATA_DIR:
    DATA_DIR = Path(DATA_DIR)
else:
    DATA_DIR = BASE_DIR.parent / "data"

# 数据库文件路径
DB_DIR = os.getenv("DB_DIR", str(DATA_DIR / "db"))
os.makedirs(DB_DIR, exist_ok=True)
DB_PATH = os.getenv("DB_PATH", str(Path(DB_DIR) / "vehicle_mgr.db"))
DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite+aiosqlite:///{DB_PATH}")

# 照片上传目录
UPLOAD_DIR = Path(os.getenv("UPLOAD_DIR", str(DATA_DIR / "photos")))
os.makedirs(UPLOAD_DIR, exist_ok=True)

# ---------- JWT ----------
SECRET_KEY = os.getenv("SECRET_KEY", "change-this-to-a-random-secret-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_HOURS = 24

# ---------- 服务器 ----------
HOST = os.getenv("HOST", "0.0.0.0")
PORT = int(os.getenv("PORT", "8700"))

# ---------- OCR ----------
OCR_ENABLED = os.getenv("OCR_ENABLED", "true").lower() == "true"

# ---------- 里程预警 ----------
MILEAGE_THRESHOLD = int(os.getenv("MILEAGE_THRESHOLD", "5000"))
