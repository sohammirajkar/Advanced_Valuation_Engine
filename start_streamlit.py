#!/usr/bin/env python3
"""
Startup script for Streamlit app on Railway
Handles port configuration properly
"""
import os
import subprocess
import sys

def main():
    print("🚀 Starting Streamlit Frontend")
    print("===============================")
    
    # Get port from environment variable, default to 8501
    port = os.environ.get('PORT', '8501')
    api_url = os.environ.get('API_URL', 'http://localhost:8000')
    
    print(f"PORT: {port}")
    print(f"API_URL: {api_url}")
    print("")
    print("⚠️  IMPORTANT: Make sure API_URL points to your deployed backend!")
    print(f"   Current API_URL: {api_url}")
    if api_url == 'http://localhost:8000':
        print("⚠️  WARNING: Using localhost - this won't work in production!")
        print("   Set API_URL environment variable to your Railway backend URL")
    print("")
    
    # Validate port is numeric
    try:
        port_int = int(port)
        print(f"Using port: {port_int}")
    except ValueError:
        print(f"Invalid port value: {port}, using default 8501")
        port_int = 8501
    
    # Build streamlit command
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
    
    print(f"Executing: {' '.join(cmd)}")
    print("")
    
    # Execute streamlit
    try:
        subprocess.run(cmd, check=True)
    except subprocess.CalledProcessError as e:
        print(f"Error starting Streamlit: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()