#!/bin/bash

# Execute the Uvicorn command using the determined port
echo "Starting Uvicorn on port: 8000"
exec uvicorn main:app --host 0.0.0.0 --port ${PORT:-8000}

