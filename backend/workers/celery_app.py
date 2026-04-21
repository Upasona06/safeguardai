"""
Celery application and task definitions.
Used for heavy async jobs: FIR PDF generation, large batch AI analysis.
"""

import logging
import sys
from pathlib import Path

                                                                                                
PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from celery import Celery
from backend.config.settings import settings

logger = logging.getLogger(__name__)

                                                                    
celery_app = Celery(
    "safeguard_ai",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
    include=["backend.workers.tasks"],
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="Asia/Kolkata",
    enable_utc=True,
    task_track_started=True,
    task_acks_late=True,
    worker_prefetch_multiplier=1,
    result_expires=3600,
)
