#!/usr/bin/env python3
"""
Celery Worker Startup Script for Railway Deployment
Starts the Celery worker for background task processing.
"""

import os
import sys
import subprocess
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def main():
    """Start Celery worker"""
    logger.info("🔄 Starting Valuation Engine Worker")
    logger.info("=" * 50)
    
    # Get environment variables
    redis_url = os.getenv('REDIS_URL')
    
    # Log configuration
    if redis_url:
        logger.info(f"Redis: Connected ✓")
    else:
        logger.error("❌ REDIS_URL not set - worker cannot start without Redis!")
        sys.exit(1)
    
    # Build Celery command
    cmd = [
        'celery', '-A', 'app.worker.celery_app', 'worker',
        '--loglevel=info',
        '--concurrency=1',
        '--pool=solo'  # Better for Railway's single-container environment
    ]
    
    logger.info(f"Executing: {' '.join(cmd)}")
    logger.info("")
    
    try:
        # Start Celery worker
        subprocess.run(cmd, check=True)
    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to start Celery worker: {e}")
        sys.exit(1)
    except KeyboardInterrupt:
        logger.info("Shutting down worker...")
        sys.exit(0)

if __name__ == "__main__":
    main()