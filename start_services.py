#!/usr/bin/env python3
"""
Startup script for the Enhanced Valuation Engine
Helps users start all required services in the correct order
"""

import subprocess
import sys
import time
import os
import signal
from typing import List, Dict


class ServiceManager:
    def __init__(self):
        self.processes: List[subprocess.Popen] = []
        self.services: Dict[str, Dict] = {
            'redis': {
                'command': ['redis-server'],
                'description': 'Redis Server (Message Broker)',
                'port': 6379,
                'required': True
            },
            'fastapi': {
                'command': ['uvicorn', 'app.main:app', '--reload', '--port', '8000'],
                'description': 'FastAPI Backend Server',
                'port': 8000,
                'required': True
            },
            'celery': {
                'command': ['celery', '-A', 'app.worker.celery_app', 'worker', '--loglevel=info'],
                'description': 'Celery Worker Process',
                'port': None,
                'required': True
            },
            'streamlit': {
                'command': ['streamlit', 'run', 'streamlit_app.py', '--server.port', '8501'],
                'description': 'Streamlit Frontend UI',
                'port': 8501,
                'required': False
            }
        }
    
    def check_dependencies(self) -> bool:
        """Check if required dependencies are installed"""
        print("🔍 Checking dependencies...")
        
        required_commands = ['redis-server', 'uvicorn', 'celery', 'streamlit']
        missing = []
        
        for cmd in required_commands:
            try:
                subprocess.run([cmd, '--help'], 
                             stdout=subprocess.DEVNULL, 
                             stderr=subprocess.DEVNULL, 
                             timeout=5)
            except (subprocess.TimeoutExpired, FileNotFoundError, subprocess.CalledProcessError):
                missing.append(cmd)
        
        if missing:
            print(f"❌ Missing commands: {', '.join(missing)}")
            print("\n💡 Install missing dependencies:")
            print("   pip install -r requirements.txt")
            print("   # For Redis, install separately based on your OS")
            print("   # macOS: brew install redis")
            print("   # Ubuntu: sudo apt-get install redis-server")
            return False
        
        print("✅ All dependencies found")
        return True
    
    def start_service(self, service_name: str) -> bool:
        """Start a single service"""
        service = self.services[service_name]
        print(f"🚀 Starting {service['description']}...")
        
        try:
            process = subprocess.Popen(
                service['command'],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                cwd=os.getcwd()
            )
            
            self.processes.append(process)
            
            # Give service time to start
            time.sleep(2)
            
            # Check if process is still running
            if process.poll() is None:
                print(f"✅ {service['description']} started successfully")
                if service['port']:
                    print(f"   Running on port {service['port']}")
                return True
            else:
                stdout, stderr = process.communicate()
                print(f"❌ {service['description']} failed to start")
                print(f"   Error: {stderr.decode()}")
                return False
                
        except Exception as e:
            print(f"❌ Failed to start {service['description']}: {e}")
            return False
    
    def start_all_services(self) -> bool:
        """Start all services in the correct order"""
        print("🚀 Enhanced Valuation Engine Startup")
        print("=" * 50)
        
        if not self.check_dependencies():
            return False
        
        # Start services in order
        service_order = ['redis', 'fastapi', 'celery', 'streamlit']
        
        for service_name in service_order:
            if not self.start_service(service_name):
                if self.services[service_name]['required']:
                    print(f"\n💥 Failed to start required service: {service_name}")
                    self.cleanup()
                    return False
                else:
                    print(f"⚠️  Optional service {service_name} failed to start, continuing...")
        
        self.show_status()
        return True
    
    def show_status(self):
        """Show the status of all services"""
        print("\n" + "=" * 50)
        print("📊 SERVICE STATUS")
        print("=" * 50)
        
        print("🔥 Redis Server       - Running on port 6379")
        print("🚀 FastAPI Backend    - http://localhost:8000")
        print("⚡ Celery Worker      - Processing background tasks")
        print("🎨 Streamlit UI       - http://localhost:8501")
        
        print("\n📚 AVAILABLE ENDPOINTS:")
        print("• API Documentation:    http://localhost:8000/docs")
        print("• Streamlit Frontend:   http://localhost:8501")
        print("• API Health Check:     http://localhost:8000/")
        
        print("\n🧪 TESTING:")
        print("• Run tests:           python test_enhanced_features.py")
        
        print("\n⏹️  SHUTDOWN:")
        print("• Press Ctrl+C to stop all services")
        
    def cleanup(self):
        """Clean up all running processes"""
        print("\n🛑 Shutting down services...")
        
        for process in self.processes:
            try:
                process.terminate()
                process.wait(timeout=5)
                print("✅ Service stopped gracefully")
            except subprocess.TimeoutExpired:
                process.kill()
                print("⚠️  Service force-killed")
            except Exception as e:
                print(f"❌ Error stopping service: {e}")
        
        print("👋 All services stopped")
    
    def run_interactive(self):
        """Run services interactively with proper cleanup"""
        try:
            if self.start_all_services():
                print("\n⌚ Services are running... Press Ctrl+C to stop")
                
                # Keep running until interrupted
                while True:
                    time.sleep(1)
                    
                    # Check if any required service has died
                    for i, process in enumerate(self.processes[:3]):  # Redis, FastAPI, Celery
                        if process.poll() is not None:
                            print(f"\n💥 Critical service died! Shutting down...")
                            self.cleanup()
                            return False
            else:
                return False
        
        except KeyboardInterrupt:
            print("\n\n🛑 Shutdown requested by user")
        finally:
            self.cleanup()
        
        return True


def main():
    """Main entry point"""
    print("🎯 Enhanced Valuation Engine Service Manager")
    print("=" * 60)
    
    manager = ServiceManager()
    
    if len(sys.argv) > 1:
        command = sys.argv[1].lower()
        
        if command == 'test':
            print("🧪 Running tests...")
            os.system('python test_enhanced_features.py')
        elif command == 'check':
            manager.check_dependencies()
        else:
            print(f"Unknown command: {command}")
            print("Available commands: test, check")
    else:
        # Interactive mode
        success = manager.run_interactive()
        sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()