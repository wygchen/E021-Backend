#!/bin/bash

# Script to run uvicorn with minimal HTTP logging for cleaner demo output
# This reduces the noise from HTTP request logs while keeping our custom INFO messages

echo "🚀 Starting HK Express Travel Agent API (Demo Mode)"
echo "📍 Running on: http://localhost:8000"
echo "📄 API Docs: http://localhost:8000/docs"
echo ""
echo "👀 Watch for green INFO messages showing agent reasoning..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Run uvicorn with:
# --log-level warning: Only show warnings/errors from uvicorn (hides INFO HTTP logs)
# --access-log: Disabled to remove HTTP request logs
# --reload: Auto-reload on file changes for development

.conda/bin/uvicorn app.question_api:app \
    --reload \
    --port 8000 \
    --log-level warning \
    --no-access-log
