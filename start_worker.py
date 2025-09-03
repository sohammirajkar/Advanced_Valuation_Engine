#!/usr/bin/env python3
"""
Celery worker startup script for Railway deployment
"""
import os
import subprocess
import sys

def main():
    print("🔄 Starting Celery Worker")
    print("=========================")
    
    redis_url = os.environ.get('REDIS_URL', 'redis://localhost:6379/0')
    
    print(f"REDIS_URL: {redis_url}")
    print("")
    
    print("Starting Celery worker...")
    print("")
    
    # Build celery command
    cmd = [
        'celery', '-A', 'app.worker.celery_app', 'worker',
        '--loglevel=info',
        '--concurrency=1'
    ]
    
    print(f"Executing: {' '.join(cmd)}")
    print("")
    
    # Execute celery
    try:
        subprocess.run(cmd, check=True)
    except subprocess.CalledProcessError as e:
        print(f"Error starting Celery worker: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()