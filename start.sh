#!/bin/bash

# Check for the dedicated application port variable first.
# If it's not set or empty, fall back to the generic $PORT variable.
# If neither is set, use 8000 as a final fallback (for local testing parity).
# Note: Railway often sets the correct port as $PORT, so this covers both bases.
APP_PORT=${RAILWAY_TCP_APPLICATION_PORT:-${PORT:-8000}}

# Execute the Uvicorn command using the determined port
echo "Starting Uvicorn on port: $APP_PORT"
exec uvicorn app.main:app --host 0.0.0.0 --port "$APP_PORT"