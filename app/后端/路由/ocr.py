"""OCR 识别 — 里程表照片公里数识别"""
import uuid
import logging
from pathlib import Path
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from pydantic import BaseModel
from models.user import User
from services.auth import get_current_user
from services.ocr import recognize_mileage
from config import UPLOAD_DIR

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/ocr", tags=["OCR"])

ALLOWED_EXT = {".jpg", ".jpeg", ".png", ".bmp", ".webp"}


class OcrResult(BaseModel):
    recognized: bool
    mileage: int | None = None
    text: str = ""


@router.post("/recognize", response_model=OcrResult)
async def ocr_recognize(
    file: UploadFile = File(...),
    user: User = Depends(get_current_user),
):
    """上传里程表照片，OCR 识别公里数"""
    # 校验文件类型
    ext = Path(file.filename).suffix.lower() if file.filename else ".jpg"
    if ext not in ALLOWED_EXT:
        raise HTTPException(400, f"不支持的文件格式: {ext}，支持 {', '.join(ALLOWED_EXT)}")

    # 保存到临时文件
    fname = f"ocr_{uuid.uuid4().hex}{ext}"
    save_path = UPLOAD_DIR / fname
    content = await file.read()
    if len(content) > 10 * 1024 * 1024:
        raise HTTPException(400, "文件过大，请上传 10MB 以内的图片")
    save_path.write_bytes(content)

    # OCR 识别
    try:
        result = await recognize_mileage(save_path)
        if result:
            logger.info(f"OCR 识别成功: {result} km, 来源: {file.filename}")
            return OcrResult(recognized=True, mileage=result, text=str(result))
        else:
            logger.info(f"OCR 未识别出有效里程: {file.filename}")
            return OcrResult(recognized=False, mileage=None, text="未识别出有效数字")
    except Exception as e:
        logger.error(f"OCR 识别异常: {e}")
        return OcrResult(recognized=False, mileage=None, text=f"识别异常: {str(e)}")
    finally:
        # 清理临时文件
        if save_path.exists():
            save_path.unlink()
