"""Analytics service — aggregates stats from MongoDB."""
import logging
from datetime import datetime, timedelta
from backend.models.schemas import AnalyticsResponse

logger = logging.getLogger(__name__)


class AnalyticsService:
    def __init__(self, db):
        self.db = db

    @staticmethod
    def _normalize_user_scope(
        user_id: str | None,
        user_email: str | None,
    ) -> tuple[str | None, str | None]:
        normalized_id = (user_id or "").strip() or None
        normalized_email = (user_email or "").strip().lower() or None
        return normalized_id, normalized_email

    @staticmethod
    def _owner_filter(user_id: str | None, user_email: str | None) -> dict:
        conditions = []
        if user_id:
            conditions.append({"owner_user_id": user_id})
        if user_email:
            conditions.append({"owner_email": user_email})

        if not conditions:
            # No identity headers means no access to shared/global analytics.
            return {"_id": None}
        if len(conditions) == 1:
            return conditions[0]
        return {"$or": conditions}

    async def get_summary(
        self,
        user_id: str | None = None,
        user_email: str | None = None,
    ) -> AnalyticsResponse:
        try:
            user_id, user_email = self._normalize_user_scope(user_id, user_email)
            owner_filter = self._owner_filter(user_id, user_email)

            total = await self.db.analyses.count_documents(owner_filter)
            critical = await self.db.analyses.count_documents({
                **owner_filter,
                "risk_level": "CRITICAL",
            })
            fir_count = await self.db.fir_reports.count_documents({
                **owner_filter,
                "status": "finalized",
            })

                                          
            daily = []
            for i in range(7, 0, -1):
                day = datetime.utcnow() - timedelta(days=i)
                day_start = day.replace(hour=0, minute=0, second=0, microsecond=0)
                day_end = day_start + timedelta(days=1)
                count = await self.db.analyses.count_documents({
                    **owner_filter,
                    "timestamp": {"$gte": day_start, "$lt": day_end}
                })
                daily.append({"date": day_start.strftime("%Y-%m-%d"), "count": count})

                                
            breakdown = {}
            for cat in ["cyberbullying", "threat", "hate_speech", "sexual_harassment", "grooming"]:
                breakdown[cat] = await self.db.analyses.count_documents(
                    {
                        **owner_filter,
                        f"labels.{cat}": {"$gt": 0.5},
                    }
                )

            return AnalyticsResponse(
                total_reports=total,
                critical_cases=critical,
                fir_generated=fir_count,
                avg_response_time=1.8,
                daily_counts=daily,
                category_breakdown=breakdown,
            )
        except Exception as e:
            logger.error("Analytics failed: %s", e)
            return AnalyticsResponse(
                total_reports=0, critical_cases=0, fir_generated=0,
                avg_response_time=0, daily_counts=[], category_breakdown={}
            )
