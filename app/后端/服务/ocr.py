"""里程表 OCR — 识别照片里的公里数（基于 Tesseract/PIL）
依赖：tesseract-ocr（系统级）、pytesseract、Pillow
"""
import re
import logging
from pathlib import Path
from config import OCR_ENABLED

logger = logging.getLogger(__name__)

# 缓存导入结果，避免每次调用都重试
_pytesseract_available = None


def _check_pytesseract():
    global _pytesseract_available
    if _pytesseract_available is not None:
        return _pytesseract_available
    try:
        import pytesseract
        # 验证 tesseract 可执行
        pytesseract.get_tesseract_version()
        _pytesseract_available = True
        logger.info("pytesseract 就绪")
    except Exception as e:
        logger.warning(f"pytesseract 不可用: {e}")
        _pytesseract_available = False
    return _pytesseract_available


async def recognize_mileage(image_path: str | Path) -> int | None:
    """识别里程表照片中的公里数，返回整数"""
    if not OCR_ENABLED:
        return None
    if not _check_pytesseract():
        return None
    try:
        from PIL import Image
        import pytesseract

        img = Image.open(str(image_path))
        # 提高识别率：转灰度 + 放大
        img = img.convert("L")
        w, h = img.size
        img = img.resize((w * 2, h * 2))

        all_text = pytesseract.image_to_string(img, lang="eng+chi_sim", config="--psm 6")
        logger.info(f"OCR 原始文本: {all_text.strip()}")

        # 找公里数模式：纯数字，3~7位
        nums = re.findall(r"\b(\d{3,7})\b", all_text)
        if not nums:
            return None
        # 取最长的数字(通常是里程数)
        nums_int = [int(n) for n in nums]
        return max(nums_int)
    except Exception as e:
        logger.error(f"OCR 识别失败: {e}")
        return None
