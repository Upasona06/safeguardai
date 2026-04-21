"""
SafeGuard AI — FastAPI Backend
Main application entry point with all routes, middleware, and startup logic.
"""

import asyncio
import logging
import sys
from contextlib import asynccontextmanager
from pathlib import Path

                                                                                            
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware

from backend.config.settings import settings
from backend.config.database import connect_db, disconnect_db, is_db_connected
from backend.routes.analysis import router as analysis_router
from backend.routes.fir import router as fir_router
from backend.routes.analytics import router as analytics_router

                                                                   
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)
logger = logging.getLogger(__name__)


                                                                   
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Minimal startup - return immediately"""
    logger.info("🚀 SafeGuard AI starting...")
    
                                                      
    import asyncio
    asyncio.create_task(connect_db())
    
    logger.info("✅ Ready (models load on first request)")
    yield
    
             
    try:
        await disconnect_db()
    except Exception:
        pass


                                                                   
app = FastAPI(
    title="SafeGuard AI",
    description="AI-powered cyber safety & FIR generation platform",
    version="3.1.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

                                                                   
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(GZipMiddleware, minimum_size=1000)

                                                                   
@app.get("/health", tags=["System"])
async def health():
    db_ok = is_db_connected()
    return {
        "status": "ok" if db_ok else "degraded",
        "version": "3.1.0",
        "service": "SafeGuard AI",
        "database": "connected" if db_ok else "unavailable",
    }


@app.get("/", tags=["System"])
async def root():
    """Root endpoint - quick health check"""
    return {
        "service": "SafeGuard AI",
        "status": "online",
        "version": "3.1.0",
        "docs": "/docs",
    }

                                                                               
app.include_router(analysis_router, tags=["Analysis"])
app.include_router(fir_router, tags=["FIR"])
app.include_router(analytics_router, tags=["Analytics"])
