"""
Async MongoDB connection via Motor.
Exposes `db` as the active database instance throughout the app.
"""

import asyncio
import logging
from fastapi import HTTPException
from motor.motor_asyncio import AsyncIOMotorClient
from backend.config.settings import settings

logger = logging.getLogger(__name__)

_client: AsyncIOMotorClient | None = None
db = None                  
_db_ready = False
_indexes_scheduled = False


async def connect_db() -> None:
    global _client, db, _db_ready, _indexes_scheduled

    try:
        if _client is None:
            _client = AsyncIOMotorClient(
                settings.MONGODB_URI,
                serverSelectionTimeoutMS=2000,
                maxPoolSize=10,
                connectTimeoutMS=2000,
            )
            db = _client[settings.MONGODB_DB]

        # Always retry ping until connection becomes healthy.
        await asyncio.wait_for(_client.admin.command("ping"), timeout=2.0)
        if not _db_ready:
            logger.info("✅ MongoDB connected")
        _db_ready = True

        if not _indexes_scheduled:
            _indexes_scheduled = True
            asyncio.create_task(_ensure_indexes())
    except asyncio.TimeoutError:
        logger.info("⚠️ MongoDB ping timeout - will retry on first request")
        _db_ready = False
    except Exception as e:
        logger.info(f"⚠️ MongoDB unavailable: {e}")
        _db_ready = False


async def disconnect_db() -> None:
    global _client, db, _db_ready, _indexes_scheduled
    if _client:
        _client.close()
        _client = None
    db = None
    _db_ready = False
    _indexes_scheduled = False
    logger.info("MongoDB disconnected")


async def _ensure_indexes() -> None:
    """Create indexes for performance and uniqueness."""
    global _indexes_scheduled

    if db is None:
        _indexes_scheduled = False
        return

    try:
        await db.analyses.create_index("id", unique=True)
        await db.analyses.create_index("created_at")
        await db.analyses.create_index("risk_level")

        await db.fir_reports.create_index("fir_id", unique=True)
        await db.fir_reports.create_index("analysis_id")
        await db.fir_reports.create_index("created_at")

        logger.info("MongoDB indexes ensured")
    except Exception as e:
        _indexes_scheduled = False
        logger.warning("MongoDB index creation failed: %s", e)


async def get_db():
    """Dependency-injection helper for FastAPI routes."""
    global _db_ready

    if not _db_ready:
                                                                               
        await connect_db()

    if not _db_ready or db is None:
        raise HTTPException(
            status_code=503,
            detail="Database unavailable. Start MongoDB or set MONGODB_URI to a reachable instance.",
        )

    return db


async def get_db_optional():
    """Best-effort DB dependency that never raises when Mongo is unavailable."""
    global _db_ready

    if not _db_ready:
        await connect_db()

    if not _db_ready or db is None:
        return None

    return db


def is_db_connected() -> bool:
    return _db_ready
