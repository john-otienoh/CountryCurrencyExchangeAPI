#!/bin/bash

PORT=${RAILWAY_TCP_APPLICATION_PORT:-${PORT:-8000}}

# Execute the Uvicorn command using the determined port
echo "Starting Uvicorn on port: $PORT"
exec eb: uvicorn main:app --host 0.0.0.0 --port $PORT
