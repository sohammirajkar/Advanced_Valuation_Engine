#!/usr/bin/env python3
"""
Backend API Startup Script for Railway Deployment
Starts the FastAPI application with Uvicorn server.
"""

import os
import sys
import subprocess
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def main():
    """Start FastAPI backend application"""
    logger.info("🚀 Starting Valuation Engine Backend API")
    logger.info("=" * 50)
    
    # Get environment variables
    port = os.getenv('PORT', '8000')
    redis_url = os.getenv('REDIS_URL')
    
    # Log configuration
    logger.info(f"Port: {port}")
    if redis_url:
        logger.info(f"Redis: Connected ✓")
    else:
        logger.warning("⚠️  REDIS_URL not set - ensure Redis service is configured!")
    
    # Validate port
    try:
        port_int = int(port)
    except ValueError:
        logger.error(f"Invalid port: {port}. Using default 8000")
        port_int = 8000
    
    # Build Uvicorn command
    cmd = [
        'uvicorn', 'app.main:app',
        '--host', '0.0.0.0',
        '--port', str(port_int),
        '--workers', '1',
        '--access-log',
        '--log-level', 'info'
    ]
    
    logger.info(f"Executing: {' '.join(cmd)}")
    logger.info("")
    
    try:
        # Start FastAPI with Uvicorn
        subprocess.run(cmd, check=True)
    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to start FastAPI: {e}")
        sys.exit(1)
    except KeyboardInterrupt:
        logger.info("Shutting down backend...")
        sys.exit(0)

if __name__ == "__main__":
    main()