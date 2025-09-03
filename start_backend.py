#!/usr/bin/env python3
"""
Backend startup script for Railway deployment
Handles FastAPI server startup with proper configuration
"""
import os
import subprocess
import sys

def main():
    print("🚀 Starting FastAPI Backend")
    print("============================")
    
    # Get port from environment variable, default to 8000
    port = os.environ.get('PORT', '8000')
    redis_url = os.environ.get('REDIS_URL', 'redis://localhost:6379/0')
    
    print(f"PORT: {port}")
    print(f"REDIS_URL: {redis_url}")
    print("")
    
    # Validate port is numeric
    try:
        port_int = int(port)
        print(f"Using port: {port_int}")
    except ValueError:
        print(f"Invalid port value: {port}, using default 8000")
        port_int = 8000
    
    print("Starting FastAPI with Uvicorn...")
    print("")
    
    # Build uvicorn command
    cmd = [
        'uvicorn', 'app.main:app',
        '--host', '0.0.0.0',
        '--port', str(port_int),
        '--workers', '1'
    ]
    
    print(f"Executing: {' '.join(cmd)}")
    print("")
    
    # Execute uvicorn
    try:
        subprocess.run(cmd, check=True)
    except subprocess.CalledProcessError as e:
        print(f"Error starting FastAPI: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()