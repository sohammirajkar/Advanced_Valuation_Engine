#!/usr/bin/env python3
"""
Frontend Startup Script for Railway Deployment
Starts the Streamlit application with proper configuration for production.
"""

import os
import sys
import subprocess
import logging
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def main():
    """Start Streamlit frontend application"""
    logger.info("🚀 Starting Valuation Engine Frontend")
    logger.info("=" * 50)
    
    # Get environment variables
    port = os.getenv('PORT', '8501')
    api_url = os.getenv('API_URL', 'http://localhost:8000')
    
    # Log configuration
    logger.info(f"Port: {port}")
    logger.info(f"API URL: {api_url}")
    
    if api_url == 'http://localhost:8000':
        logger.warning("⚠️  Using localhost API URL - ensure backend is deployed and API_URL is set!")
    
    # Validate port
    try:
        port_int = int(port)
    except ValueError:
        logger.error(f"Invalid port: {port}. Using default 8501")
        port_int = 8501
    
    # Build Streamlit command
    cmd = [
        'streamlit', 'run', 'streamlit_app.py',
        '--server.port', str(port_int),
        '--server.address', '0.0.0.0',
        '--server.headless', 'true',
        '--server.fileWatcherType', 'none',
        '--browser.gatherUsageStats', 'false',
        '--server.enableCORS', 'false',
        '--server.enableXsrfProtection', 'false'
    ]
    
    logger.info(f"Executing: {' '.join(cmd)}")
    logger.info("")
    
    try:
        # Start Streamlit
        subprocess.run(cmd, check=True)
    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to start Streamlit: {e}")
        sys.exit(1)
    except KeyboardInterrupt:
        logger.info("Shutting down frontend...")
        sys.exit(0)

if __name__ == "__main__":
    main()