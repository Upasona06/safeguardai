"""
Celery task definitions.
Heavy AI processing and FIR PDF generation run here asynchronously.
"""

import logging
import asyncio
from backend.workers.celery_app import celery_app

logger = logging.getLogger(__name__)


                                                                    
def run_async(coro):
    """Run an async coroutine from a sync Celery task."""
    loop = asyncio.new_event_loop()
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()


                                                                   
@celery_app.task(
    bind=True,
    name="tasks.analyze_text_async",
    max_retries=3,
    default_retry_delay=5,
)
def analyze_text_async(self, text: str, analysis_id: str):
    """
    Background task for heavy text analysis.
    Stores result in MongoDB; frontend polls for completion.
    """
    try:
        from backend.config.database import connect_db, db
        from backend.services.analysis_service import AnalysisService

        run_async(connect_db())
        service = AnalysisService(db)
        result = run_async(service.analyze_text(text))
        logger.info("Async text analysis complete: %s", result.id)
        return {"status": "complete", "analysis_id": result.id}

    except Exception as exc:
        logger.error("analyze_text_async failed: %s", exc)
        raise self.retry(exc=exc)


                                                                   
@celery_app.task(
    bind=True,
    name="tasks.generate_fir_async",
    max_retries=2,
    default_retry_delay=10,
)
def generate_fir_async(self, fir_payload: dict):
    """
    Background task for FIR PDF generation.
    Takes a FinalizeFIRRequest-compatible dict.
    """
    try:
        from backend.config.database import connect_db, db
        from backend.services.fir_service import FIRService
        from backend.models.schemas import FinalizeFIRRequest

        run_async(connect_db())
        service = FIRService(db)
        data = FinalizeFIRRequest(**fir_payload)
        pdf_url = run_async(service.generate_fir_pdf(data))
        logger.info("Async FIR PDF generated: %s → %s", data.fir_id, pdf_url)
        return {"status": "complete", "pdf_url": pdf_url}

    except Exception as exc:
        logger.error("generate_fir_async failed: %s", exc)
        raise self.retry(exc=exc)


                                                                    
@celery_app.task(
    bind=True,
    name="tasks.batch_image_analysis",
    max_retries=2,
)
def batch_image_analysis(self, image_urls: list):
    """
    Analyze multiple images in batch.
    Downloads from Cloudinary URLs, runs OCR + classification.
    """
    import httpx

    results = []
    for url in image_urls:
        try:
            response = httpx.get(url, timeout=15)
            image_bytes = response.content

            from backend.utils.ocr import extract_text_from_image
            from ai_services.toxicity import ToxicityClassifier

            text = extract_text_from_image(image_bytes)
            clf = ToxicityClassifier()
            scores = clf.classify(text) if text else {}
            results.append({"url": url, "extracted_text": text, "scores": scores})
        except Exception as e:
            logger.error("Batch image failed for %s: %s", url, e)
            results.append({"url": url, "error": str(e)})

    return results
