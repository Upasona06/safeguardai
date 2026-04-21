#!/bin/bash
# Startup script for Render - handles Python path correctly
export PYTHONPATH="${PYTHONPATH}:/opt/render/project/src"
cd /opt/render/project/src
python -m uvicorn backend.main:app --host 0.0.0.0 --port $PORT
