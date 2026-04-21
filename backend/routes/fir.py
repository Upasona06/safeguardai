"""
FIR routes: /generate-fir, /finalize-fir, /download-fir/{fir_id}
"""

import logging
import os
from fastapi import APIRouter, HTTPException, Depends, Request
from fastapi.responses import FileResponse, RedirectResponse

from backend.models.schemas import (
    GenerateFIRRequest,
    FinalizeFIRRequest,
    FIRCreateResponse,
    FIRFinalizeResponse,
)
from backend.services.fir_service import FIRService
from backend.config.database import get_db_optional
from backend.config.settings import settings

logger = logging.getLogger(__name__)
router = APIRouter()


def get_fir_service(db=Depends(get_db_optional)) -> FIRService:
    return FIRService(db)


def _extract_user_scope(request: Request) -> tuple[str | None, str | None]:
    """Read user identity from headers (and query params for file-download fallback)."""
    user_id = (
        request.headers.get("x-user-id")
        or request.query_params.get("user_id")
        or ""
    ).strip() or None

    raw_email = (
        request.headers.get("x-user-email")
        or request.query_params.get("user_email")
        or ""
    ).strip()
    user_email = raw_email.lower() if raw_email else None
    return user_id, user_email


                                                                    
@router.post("/generate-fir", response_model=FIRCreateResponse)
async def generate_fir(
    request: Request,
    body: GenerateFIRRequest,
    service: FIRService = Depends(get_fir_service),
):
    """
    Create a FIR record linked to an analysis result.
    Returns a fir_id for subsequent finalization and download.
    """
    try:
        user_id, user_email = _extract_user_scope(request)
        fir_id = await service.create_fir_record(
            body.analysis_id,
            user_id=user_id,
            user_email=user_email,
        )
        return FIRCreateResponse(
            fir_id=fir_id,
            message="FIR record created. Call /finalize-fir to generate the PDF.",
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.exception("FIR creation failed")
        raise HTTPException(status_code=500, detail=str(e))


                                                                    
@router.post("/finalize-fir", response_model=FIRFinalizeResponse)
async def finalize_fir(
    request: Request,
    body: FinalizeFIRRequest,
    service: FIRService = Depends(get_fir_service),
):
    """
    Generate a court-ready FIR PDF using ReportLab, upload to Cloudinary,
    store metadata in MongoDB.
    """
    try:
        user_id, user_email = _extract_user_scope(request)
        pdf_url = await service.generate_fir_pdf(
            body,
            user_id=user_id,
            user_email=user_email,
        )
        return FIRFinalizeResponse(fir_id=body.fir_id, pdf_url=pdf_url)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.exception("FIR PDF generation failed")
        raise HTTPException(status_code=500, detail=str(e))


                                                                    
@router.get("/download-fir/{fir_id}")
async def download_fir(
    request: Request,
    fir_id: str,
    service: FIRService = Depends(get_fir_service),
):
    """
    Stream the FIR PDF for download.
    Falls back to local file if Cloudinary URL unavailable.
    """
    try:
        user_id, user_email = _extract_user_scope(request)
        pdf_path, pdf_url = await service.get_fir_download_targets(
            fir_id,
            user_id=user_id,
            user_email=user_email,
        )

                                         
        if pdf_path and os.path.exists(pdf_path):
            return FileResponse(
                path=pdf_path,
                media_type="application/pdf",
                filename=f"FIR_{fir_id}.pdf",
                headers={"Content-Disposition": f'attachment; filename="FIR_{fir_id}.pdf"'},
            )

                                                                         
        if pdf_url:
            return RedirectResponse(url=pdf_url, status_code=307)

        raise HTTPException(status_code=404, detail="FIR PDF not found")
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.exception("FIR download failed")
        raise HTTPException(status_code=500, detail=str(e))


                                                                   
@router.get("/fir-history")
async def get_fir_history(
    request: Request,
    limit: int = 50,
    skip: int = 0,
    service: FIRService = Depends(get_fir_service),
):
    """
    Fetch FIR history with pagination.
    Returns list of FIRs sorted by creation date (newest first).
    """
    try:
        user_id, user_email = _extract_user_scope(request)
        return await service.get_fir_history(
            limit=limit,
            skip=skip,
            user_id=user_id,
            user_email=user_email,
        )
    except Exception as e:
        logger.exception("FIR history fetch failed")
        raise HTTPException(status_code=500, detail=str(e))
