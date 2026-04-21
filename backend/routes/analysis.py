"""
Analysis routes: /analyze-text, /analyze-image, /analyze-context
All heavy lifting is delegated to service layer.
"""

import asyncio
import logging
from fastapi import APIRouter, File, UploadFile, HTTPException, Depends
from fastapi.responses import JSONResponse

from backend.models.schemas import (
    TextAnalysisRequest,
    ContextAnalysisRequest,
    AnalysisResponse,
)
from backend.services.analysis_service import AnalysisService
from backend.services.cloudinary_service import CloudinaryService
from backend.config.database import get_db_optional
from backend.config.settings import settings

logger = logging.getLogger(__name__)
router = APIRouter()


def get_analysis_service(db=Depends(get_db_optional)) -> AnalysisService:
    return AnalysisService(db)


                                                                    
@router.post("/analyze-text", response_model=AnalysisResponse)
async def analyze_text(
    body: TextAnalysisRequest,
    service: AnalysisService = Depends(get_analysis_service),
):
    """
    Analyze raw text for harmful content.
    Returns multi-label scores, risk level, highlighted text, and legal mappings.
    """
    try:
        logger.info("Text analysis request: %d chars", len(body.text))
        result = await service.analyze_text(body.text)
        return result
    except Exception as e:
        logger.exception("Text analysis failed")
        raise HTTPException(status_code=500, detail=str(e))


                                                                    
@router.post("/analyze-image", response_model=AnalysisResponse)
async def analyze_image(
    file: UploadFile = File(...),
    service: AnalysisService = Depends(get_analysis_service),
):
    """
    Accept an image upload, run Tesseract OCR, upload to Cloudinary,
    then analyze extracted text + visual content.
    """
    if file.size and file.size > settings.MAX_UPLOAD_BYTES:
        raise HTTPException(status_code=413, detail="File too large (max 10 MB)")

    allowed_types = {"image/jpeg", "image/png", "image/webp", "image/gif"}
    if file.content_type not in allowed_types:
        raise HTTPException(status_code=415, detail="Unsupported image type")

    try:
        file_bytes = await file.read()
        logger.info("Image analysis: %s (%d bytes)", file.filename, len(file_bytes))

        cloudinary_service = CloudinaryService()
        upload_task = asyncio.create_task(cloudinary_service.upload_bytes(
            file_bytes, folder="evidence", filename=file.filename or "upload"
        ))

        try:
            # Run OCR + AI inference immediately; do not block on network upload first.
            result = await service.analyze_image(file_bytes, image_url=None)
        except Exception:
            upload_task.cancel()
            raise

        try:
            image_url = await upload_task
            if image_url:
                result.image_url = image_url
        except Exception as upload_error:
            logger.warning("Image upload failed after analysis completion: %s", upload_error)

        return result

    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Image analysis failed")
        raise HTTPException(status_code=500, detail=str(e))


                                                                    
@router.post("/analyze-context", response_model=AnalysisResponse)
async def analyze_context(
    body: ContextAnalysisRequest,
    service: AnalysisService = Depends(get_analysis_service),
):
    """
    Analyze a full conversation thread for escalation patterns,
    grooming, sustained harassment, etc.
    """
    try:
        logger.info("Context analysis: %d messages", len(body.messages))
        result = await service.analyze_context(body.messages)
        return result
    except Exception as e:
        logger.exception("Context analysis failed")
        raise HTTPException(status_code=500, detail=str(e))
