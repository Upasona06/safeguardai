"""
Minimal FastAPI app for Render deployment.
Routes loaded eagerly (fast), models loaded lazily (on first request).
"""

import asyncio
import logging
from contextlib import asynccontextmanager
from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from backend.config.settings import settings
from backend.config.database import connect_db, disconnect_db
from backend.routes.analysis import router as analysis_router
from backend.routes.fir import router as fir_router
from backend.routes.analytics import router as analytics_router

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

                           
_db_connected = False


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Minimal lifespan for fast startup"""
    logger.info("🚀 SafeGuard AI starting...")
    
                                             
    asyncio.create_task(_connect_db_bg())
    
    logger.info("✅ Startup complete - listening for requests")
    yield
    logger.info("🛑 Shutting down...")
    await disconnect_db()


async def _connect_db_bg():
    """Connect to DB in background"""
    global _db_connected
    try:
        await asyncio.wait_for(connect_db(), timeout=5)
        _db_connected = True
        logger.info("✅ Database connected")
    except asyncio.TimeoutError:
        logger.warning("⚠️  Database connection timeout (will retry on first request)")
    except Exception as e:
        logger.error(f"❌ Database connection failed: {e}")


app = FastAPI(
    title="SafeGuard AI",
    description="AI-powered cyber safety platform",
    version="3.1.0",
    lifespan=lifespan,
)

                                                                              
app.include_router(analysis_router, tags=["Analysis"])
app.include_router(fir_router, tags=["FIR"])
app.include_router(analytics_router, tags=["Analytics"])

            
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(GZipMiddleware, minimum_size=1000)


                                     
@app.get("/", tags=["System"])
async def root():
    """Instant response - app is alive"""
    return {
        "service": "SafeGuard AI",
        "status": "online",
        "version": "3.1.0",
    }


@app.get("/health", tags=["System"])
async def health():
    """Health check - instant response"""
    return {
        "status": "ok",
        "service": "SafeGuard AI",
        "database": "connected" if _db_connected else "connecting",
    }


@app.get("/status", tags=["System"])
async def status():
    """Detailed status"""
    return {
        "app": "SafeGuard AI",
        "version": "3.1.0",
        "database": "connected" if _db_connected else "connecting",
        "routes": "ready",
    }
