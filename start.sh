#!/bin/bash
echo "Starting FastAPI..."
exec uvicorn main:app --host 0.0.0.0 --port ${PORT:-8000}

