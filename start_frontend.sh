#!/bin/bash

echo "🚀 Starting Streamlit Frontend"
echo "==============================="
echo "PORT: ${PORT:-8501}"
echo "API_URL: ${API_URL:-http://localhost:8000}"
echo ""

# Start Streamlit with proper configuration
exec streamlit run streamlit_app.py \
    --server.port=${PORT:-8501} \
    --server.address=0.0.0.0 \
    --server.headless=true \
    --server.fileWatcherType=none \
    --browser.gatherUsageStats=false \
    --server.enableCORS=false \
    --server.enableXsrfProtection=false