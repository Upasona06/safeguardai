"""Analytics route: GET /analytics"""

import logging
from fastapi import APIRouter, Depends, Request
from backend.models.schemas import AnalyticsResponse
from backend.services.analytics_service import AnalyticsService
from backend.config.database import get_db_optional

logger = logging.getLogger(__name__)
router = APIRouter()


def _extract_user_scope(request: Request) -> tuple[str | None, str | None]:
    user_id = (request.headers.get("x-user-id") or "").strip() or None
    raw_email = (request.headers.get("x-user-email") or "").strip()
    user_email = raw_email.lower() if raw_email else None
    return user_id, user_email


@router.get("/analytics", response_model=AnalyticsResponse)
async def get_analytics(request: Request, db=Depends(get_db_optional)):
    """Return analytics summary scoped to the requesting user."""
    service = AnalyticsService(db)
    user_id, user_email = _extract_user_scope(request)
    return await service.get_summary(user_id=user_id, user_email=user_email)
