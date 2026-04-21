"""
OCR utility — extracts text from image bytes using ensemble of engines.

Optimized pipeline:
  1. Preprocess image (contrast, deskew, upscale)
    2. Run PaddleOCR as PRIMARY engine
    3. Fallback to EasyOCR
    4. Tesseract tertiary fallback
"""

import logging
from io import BytesIO
import re
import hashlib
import time
import shutil

logger = logging.getLogger(__name__)

from backend.config.settings import settings

                                                                    
_paddle_ocr = None
_easyocr_reader = None
_tesseract_available: bool | None = None
_OCR_CACHE: dict[str, tuple[float, str]] = {}
_OCR_CACHE_TTL_SEC = 300
_OCR_CACHE_MAX_ITEMS = 64


def _is_tesseract_available() -> bool:
    """Cache whether the tesseract binary is available in runtime PATH."""
    global _tesseract_available
    if _tesseract_available is None:
        _tesseract_available = bool(shutil.which("tesseract"))
        if not _tesseract_available:
            logger.warning("Tesseract binary not found in PATH; OCR will rely on Paddle/EasyOCR fallbacks")
    return _tesseract_available


def _get_paddle_ocr():
    """Lazy-load PaddleOCR to avoid startup overhead."""
    global _paddle_ocr
    if _paddle_ocr is None:
        try:
            from paddleocr import PaddleOCR
            try:
                _paddle_ocr = PaddleOCR(
                    lang="en",
                    show_log=False,
                    use_doc_orientation_classify=False,
                    use_doc_unwarping=False,
                    use_textline_orientation=False,
                )
            except TypeError:
                                                                         
                _paddle_ocr = PaddleOCR(use_angle_cls=False, lang="en", show_log=False)
            logger.info("✅ PaddleOCR initialized")
        except Exception as e:
            logger.warning("PaddleOCR unavailable (%s)", e)
            _paddle_ocr = False                                 
    return _paddle_ocr if _paddle_ocr is not False else None


def _get_easyocr_reader():
    """Lazy-load EasyOCR reader to avoid startup overhead."""
    global _easyocr_reader
    if _easyocr_reader is None:
        try:
            import easyocr

            _easyocr_reader = easyocr.Reader(["en"], gpu=False, verbose=False)
            logger.info("✅ EasyOCR initialized")
        except Exception as e:
            logger.warning("EasyOCR unavailable (%s)", e)
            _easyocr_reader = False
    return _easyocr_reader if _easyocr_reader is not False else None


def _preprocess_image(image):
    """
    Preprocess image for better OCR accuracy.
    Handles contrast, deskew, and binarization for handwritten text.
    """
    try:
        from PIL import Image, ImageEnhance, ImageFilter, ImageOps

                                                    
        image = ImageOps.exif_transpose(image)

                                                                                
        image = image.convert("L")
        w, h = image.size
        max_dim = max(w, h)

        # Keep OCR workload bounded on very large uploads.
        if max_dim > settings.OCR_MAX_DIM:
            scale = settings.OCR_MAX_DIM / float(max_dim)
            new_w = max(1, int(w * scale))
            new_h = max(1, int(h * scale))
            image = image.resize((new_w, new_h), resample=Image.Resampling.LANCZOS)
            w, h = image.size
            max_dim = max(w, h)

        # Mild upscale helps small screenshots while keeping latency reasonable.
        if max_dim < settings.OCR_UPSCALE_MIN_DIM:
            scale = max(1.0, settings.OCR_UPSCALE_FACTOR)
            image = image.resize((int(w * scale), int(h * scale)), resample=Image.Resampling.LANCZOS)

                                                               
        image = ImageOps.autocontrast(image)
        image = ImageEnhance.Contrast(image).enhance(1.8)
        image = image.filter(ImageFilter.MedianFilter(size=3))

        return image
    except Exception as e:
        logger.warning("Image preprocessing failed (%s), proceeding without it", e)
        return image


def _pil_to_ocr_bytes(image: "Image") -> bytes:
    """Encode PIL image losslessly to preserve text edges for OCR."""
    buffer = BytesIO()
    image.save(buffer, format="PNG", optimize=True)
    return buffer.getvalue()


def _ocr_cache_get(key: str) -> str | None:
    cached = _OCR_CACHE.get(key)
    if not cached:
        return None

    created_at, text = cached
    if time.time() - created_at > _OCR_CACHE_TTL_SEC:
        _OCR_CACHE.pop(key, None)
        return None
    return text


def _ocr_cache_set(key: str, text: str) -> None:
    if len(_OCR_CACHE) >= _OCR_CACHE_MAX_ITEMS:
        oldest_key = min(_OCR_CACHE.items(), key=lambda item: item[1][0])[0]
        _OCR_CACHE.pop(oldest_key, None)
    _OCR_CACHE[key] = (time.time(), text)


def _crop_text_region(image):
    """Crop likely text region to improve OCR on images with large empty margins."""
    try:
        import cv2
        import numpy as np

        gray = np.array(image.convert("L"))
        blurred = cv2.GaussianBlur(gray, (3, 3), 0)
        _, thresh = cv2.threshold(
            blurred, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU
        )

        contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        boxes = []
        for contour in contours:
            area = cv2.contourArea(contour)
            if area < 80:
                continue
            x, y, w, h = cv2.boundingRect(contour)
            if w < 8 or h < 8:
                continue
            boxes.append((x, y, w, h))

        if not boxes:
            return image

        x1 = min(b[0] for b in boxes)
        y1 = min(b[1] for b in boxes)
        x2 = max(b[0] + b[2] for b in boxes)
        y2 = max(b[1] + b[3] for b in boxes)

        pad = 24
        img_w, img_h = image.size
        left = max(0, x1 - pad)
        top = max(0, y1 - pad)
        right = min(img_w, x2 + pad)
        bottom = min(img_h, y2 + pad)

        if right - left < 30 or bottom - top < 20:
            return image

        return image.crop((left, top, right, bottom))
    except Exception as e:
        logger.warning("Text region crop skipped: %s", e)
        return image


def _extract_with_tesseract(image: "Image") -> str:
    """
    Extract text using Tesseract OCR with enhanced PSM for handwriting.
    """
    try:
        if not _is_tesseract_available():
            return ""

        import pytesseract

        variants = [("base", image)]
        configs = [
            "--psm 6 --oem 3",
            "--psm 11 --oem 3",
        ]

        best_text = ""
        for variant_name, variant_image in variants:
            for cfg in configs:
                try:
                    text = pytesseract.image_to_string(
                        variant_image,
                        lang="eng",
                        config=f"{cfg} --dpi 300",
                    ).strip()
                    if len(text) > len(best_text):
                        best_text = text
                    if len(text) >= 4 and any(ch.isalpha() for ch in text):
                        logger.info(
                            "Tesseract extracted %d chars using %s | %s",
                            len(text),
                            variant_name,
                            cfg,
                        )
                        return text
                except pytesseract.pytesseract.TesseractError:
                    continue

        if best_text:
            logger.info("Tesseract fallback extracted %d chars", len(best_text))
            return best_text
        
        logger.warning("Tesseract extraction yielded no text")
        return ""
    except Exception as e:
        logger.error("Tesseract extraction failed: %s", e)
        return ""


def _extract_with_paddle(image_bytes: bytes) -> str:
    """
    Extract text using PaddleOCR (better for handwriting & complex layouts).
    """
    try:
        paddle_ocr = _get_paddle_ocr()
        if paddle_ocr is None:
            return ""

        import cv2
        import numpy as np

        image_array = np.frombuffer(image_bytes, dtype=np.uint8)
        image = cv2.imdecode(image_array, cv2.IMREAD_COLOR)
        if image is None:
            return ""

        try:
            result = paddle_ocr.ocr(image, cls=False)
        except Exception:
            # Keep compatibility with older PaddleOCR variants.
            result = paddle_ocr.ocr(image, cls=True)

        text_parts = []

        if result and isinstance(result, list) and isinstance(result[0], dict):
            for page in result:
                rec_texts = page.get("rec_texts") or []
                text_parts.extend([t for t in rec_texts if t])
        else:
            for line in result or []:
                for word_info in line:
                    if word_info and len(word_info) >= 2:
                        text_parts.append(word_info[1][0])

        text = " ".join(text_parts).strip()
        if text:
            logger.info("PaddleOCR extracted %d characters", len(text))
        return text
    except Exception as e:
        logger.warning("PaddleOCR extraction failed: %s", e)
        return ""


def _extract_with_easyocr(image_bytes: bytes) -> str:
    """Extract text using EasyOCR fallback."""
    try:
        import cv2
        import numpy as np

        reader = _get_easyocr_reader()
        if reader is None:
            return ""

        image_array = np.frombuffer(image_bytes, dtype=np.uint8)
        image = cv2.imdecode(image_array, cv2.IMREAD_COLOR)
        if image is None:
            return ""

        pieces = reader.readtext(image, detail=0, paragraph=True)
        text = " ".join(t.strip() for t in pieces if isinstance(t, str) and t.strip()).strip()
        if text:
            logger.info("EasyOCR extracted %d characters", len(text))
        return text
    except Exception as e:
        logger.warning("EasyOCR extraction failed: %s", e)
        return ""


def _postprocess_ocr_text(text: str) -> str:
    """Normalize OCR output artifacts before downstream NLP classification."""
    if not text:
        return ""

    normalized = text
    normalized = re.sub(r"[\r\n\t]+", " ", normalized)
    normalized = re.sub(r"\s+", " ", normalized).strip()

                                                                            
    normalized = re.sub(
        r"\b(?:[a-zA-Z]\s+){2,}[a-zA-Z]\b",
        lambda m: m.group(0).replace(" ", ""),
        normalized,
    )

    return normalized


def extract_text_from_image(image_bytes: bytes) -> str:
    """
    OCR extraction using production fallback order.

    Pipeline:
    1. Preprocess image (contrast, deskew, upscale)
    2. PaddleOCR primary + raw-image retry
    3. Tesseract fallback
    4. EasyOCR fallback (optional)
    """
    try:
        from PIL import Image

        image_hash = hashlib.md5(image_bytes).hexdigest()
        cached_text = _ocr_cache_get(image_hash)
        if cached_text is not None:
            logger.info("OCR cache hit: %d chars", len(cached_text))
            return cached_text

        started_at = time.perf_counter()

        def _time_budget_exceeded() -> bool:
            return (time.perf_counter() - started_at) >= settings.OCR_FALLBACK_TIME_BUDGET_SEC

        image = Image.open(BytesIO(image_bytes))

                                  
        if image.mode not in ("RGB", "L"):
            image = image.convert("RGB")

        original_image = image.copy()
        processed_image = _preprocess_image(image)
        processed_bytes = _pil_to_ocr_bytes(processed_image)
        original_bytes = _pil_to_ocr_bytes(original_image)

                                              
        logger.info("OCR Stage 1: PaddleOCR primary")
        text = _extract_with_paddle(processed_bytes)
        if text:
            logger.info("✅ PaddleOCR primary extracted %d chars", len(text))
            final_text = _postprocess_ocr_text(text)
            _ocr_cache_set(image_hash, final_text)
            return final_text

        logger.info("OCR Stage 1b: PaddleOCR raw-image retry")
        text = _extract_with_paddle(original_bytes)
        if text:
            logger.info("✅ PaddleOCR raw-image retry extracted %d chars", len(text))
            final_text = _postprocess_ocr_text(text)
            _ocr_cache_set(image_hash, final_text)
            return final_text

        if _time_budget_exceeded():
            logger.warning("OCR time budget reached after Paddle stage")
            return ""

        # Crop only for fallback path to keep fast-path latency lower.
        cropped_image = _crop_text_region(processed_image)

        if _is_tesseract_available():
            logger.info("OCR Stage 2: Tesseract fallback")
            text = _extract_with_tesseract(processed_image)
            if not text:
                text = _extract_with_tesseract(cropped_image)
            if not text:
                text = _extract_with_tesseract(original_image)

            if text:
                logger.info("✅ Tesseract fallback extracted %d chars", len(text))
                final_text = _postprocess_ocr_text(text)
                _ocr_cache_set(image_hash, final_text)
                return final_text
        else:
            logger.info("OCR Stage 2 skipped: Tesseract binary unavailable")

        if _time_budget_exceeded():
            logger.warning("OCR time budget reached before EasyOCR stage")
            return ""

        should_try_easyocr = settings.OCR_ENABLE_EASYOCR_FALLBACK or not _is_tesseract_available()
        if should_try_easyocr:
            logger.info("OCR Stage 3: EasyOCR fallback")
            text = _extract_with_easyocr(processed_bytes)
            if not text:
                text = _extract_with_easyocr(original_bytes)
            if text:
                logger.info("✅ EasyOCR fallback extracted %d chars", len(text))
                final_text = _postprocess_ocr_text(text)
                _ocr_cache_set(image_hash, final_text)
                return final_text
        
        logger.warning("All OCR engines failed")
        return ""

    except ImportError as e:
        logger.error("Required OCR dependencies not installed: %s", e)
        return ""
    except Exception as e:
        logger.error("OCR pipeline failed: %s", e)
        return ""
