"""
WSGI Entry Point for Render Deployment
Uses minimal app for fast startup, routes load asynchronously in background
"""
import os
import sys
from pathlib import Path

                                       
PROJECT_ROOT = Path(__file__).resolve().parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

                                  
from backend.app_minimal import app

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port, loop="uvloop")
