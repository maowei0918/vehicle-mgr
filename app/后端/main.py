"""车辆管理系统 - FastAPI 入口"""
import sys
import logging
from pathlib import Path
from contextlib import asynccontextmanager

# 添加第三方库路径（如 openpyxl）
_extra_lib = Path(__file__).parent.parent / "pylib"
if _extra_lib.is_dir():
    sys.path.insert(0, str(_extra_lib.resolve()))

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse
from fastapi.middleware.cors import CORSMiddleware

from database import init_db
from config import UPLOAD_DIR, DATA_DIR, DB_PATH, BACKUP_DIR, BACKUP_INTERVAL_HOURS, BACKUP_RETENTION, HOST, PORT

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    logging.info("数据库初始化完成")
    # 启动自动备份调度器
    try:
        from backup_scheduler import start_scheduler

        settings_cache = {
            "BACKUP_INTERVAL_HOURS": str(BACKUP_INTERVAL_HOURS),
            "BACKUP_RETENTION": str(BACKUP_RETENTION),
        }

        def get_settings():
            # 尝试从 settings 模块读取最新设置（如果已注册则路由会处理）
            return settings_cache

        start_scheduler(DATA_DIR, DB_PATH, UPLOAD_DIR, get_settings)
        logging.info("自动备份调度器已启动")
    except Exception as e:
        logging.warning(f"自动备份调度器启动失败: {e}")
    yield


app = FastAPI(title="车辆管理系统", version="1.0", lifespan=lifespan)

# CORS — 允许小程序访问
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 静态文件 — 照片访问
app.mount("/uploads", StaticFiles(directory=str(UPLOAD_DIR)), name="uploads")
app.mount("/admin", StaticFiles(directory=str(Path(__file__).resolve().parent / "webadmin"), html=True), name="admin")

# 注册路由
from routers import auth, group_user, vehicle, inspection, repair, settings, contract_part, contract, repair_flow, operation_log, role, ocr, backup
app.include_router(auth.router)
app.include_router(group_user.router)
app.include_router(vehicle.router)
app.include_router(inspection.router)
app.include_router(repair.router)
app.include_router(settings.router)
app.include_router(contract_part.router)
app.include_router(contract.router)
app.include_router(repair_flow.router)
app.include_router(operation_log.router)
app.include_router(role.router)
app.include_router(ocr.router)
app.include_router(backup.router)


@app.get("/api/health")
async def health():
    return {"status": "ok"}


@app.get("/")
async def root():
    return RedirectResponse(url="/admin/index.html")


def main():
    import uvicorn
    uvicorn.run("main:app", host=HOST, port=PORT, reload=False)


if __name__ == "__main__":
    main()
