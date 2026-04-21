"""Analytics route: GET /analytics"""

import logging
from fastapi import APIRouter, Depends
from backend.models.schemas import AnalyticsResponse
from backend.services.analytics_service import AnalyticsService
from backend.config.database import get_db_optional

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/analytics", response_model=AnalyticsResponse)
async def get_analytics(db=Depends(get_db_optional)):
    """Return platform-wide analytics summary."""
    service = AnalyticsService(db)
    return await service.get_summary()
