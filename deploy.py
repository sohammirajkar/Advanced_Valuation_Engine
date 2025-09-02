#!/usr/bin/env python3
"""
Enhanced Valuation Engine Deployment Script
Supports multiple deployment targets: local, docker, and AWS
"""

import subprocess
import sys
import os
import json
import time
from pathlib import Path
from typing import Dict, List, Optional


class DeploymentManager:
    def __init__(self):
        self.project_root = Path(__file__).parent
        self.terraform_dir = self.project_root / "terraform"
        
    def check_prerequisites(self, deployment_type: str) -> bool:
        """Check if required tools are installed"""
        print(f"🔍 Checking prerequisites for {deployment_type} deployment...")
        
        requirements = {
            'local': ['python', 'redis-server'],
            'docker': ['docker', 'docker-compose'],
            'aws': ['terraform', 'aws', 'docker']
        }
        
        missing = []
        for tool in requirements.get(deployment_type, []):
            try:
                subprocess.run([tool, '--version'], 
                             stdout=subprocess.DEVNULL, 
                             stderr=subprocess.DEVNULL, 
                             timeout=5)
            except (subprocess.TimeoutExpired, FileNotFoundError):
                missing.append(tool)
        
        if missing:
            print(f"❌ Missing tools: {', '.join(missing)}")
            self._show_installation_instructions(missing)
            return False
        
        print("✅ All prerequisites satisfied")
        return True
    
    def _show_installation_instructions(self, missing_tools: List[str]):
        """Show installation instructions for missing tools"""
        instructions = {
            'docker': 'Install Docker Desktop from https://docker.com/products/docker-desktop',
            'docker-compose': 'Install Docker Compose (usually included with Docker Desktop)',
            'terraform': 'Install Terraform from https://terraform.io/downloads',
            'aws': 'Install AWS CLI: pip install awscli',
            'redis-server': 'macOS: brew install redis | Ubuntu: sudo apt install redis-server'
        }
        
        print("\n💡 Installation instructions:")
        for tool in missing_tools:
            if tool in instructions:
                print(f"   {tool}: {instructions[tool]}")
    
    def deploy_local(self) -> bool:
        """Deploy locally using the start_services script"""
        print("🚀 Starting local deployment...")
        
        if not self.check_prerequisites('local'):
            return False
        
        try:
            # Install dependencies
            print("📦 Installing Python dependencies...")
            subprocess.run([sys.executable, '-m', 'pip', 'install', '-r', 'requirements.txt'], 
                         check=True)
            
            # Start Redis if not running
            try:
                subprocess.run(['redis-cli', 'ping'], 
                             stdout=subprocess.DEVNULL, 
                             stderr=subprocess.DEVNULL, 
                             timeout=2)
                print("✅ Redis already running")
            except:
                print("🚀 Starting Redis...")
                subprocess.run(['redis-server', '--daemonize', 'yes'], check=True)
            
            print("🎯 Local deployment ready!")
            print("\n📋 Next steps:")
            print("   1. Start FastAPI: uvicorn app.main:app --reload --port 8000")
            print("   2. Start Celery: celery -A app.worker.celery_app worker --loglevel=info")
            print("   3. Start Streamlit: streamlit run streamlit_app.py")
            print("\n🌐 Access URLs:")
            print("   • API: http://localhost:8000")
            print("   • Streamlit UI: http://localhost:8501")
            print("   • API Docs: http://localhost:8000/docs")
            
            return True
            
        except Exception as e:
            print(f"❌ Local deployment failed: {e}")
            return False
    
    def deploy_docker(self) -> bool:
        """Deploy using Docker Compose"""
        print("🐳 Starting Docker deployment...")
        
        if not self.check_prerequisites('docker'):
            return False
        
        try:
            # Build and start services
            print("🏗️  Building Docker images...")
            subprocess.run(['docker-compose', 'build'], check=True)
            
            print("🚀 Starting services...")
            subprocess.run(['docker-compose', 'up', '-d'], check=True)
            
            # Wait for services to be ready
            print("⏳ Waiting for services to start...")
            time.sleep(10)
            
            # Check service status
            result = subprocess.run(['docker-compose', 'ps'], 
                                  capture_output=True, text=True)
            print("📊 Service Status:")
            print(result.stdout)
            
            print("\n🎯 Docker deployment completed!")
            print("\n🌐 Access URLs:")
            print("   • API: http://localhost:8000")
            print("   • Streamlit UI: http://localhost:8501")
            print("   • API Docs: http://localhost:8000/docs")
            print("   • Celery Flower: http://localhost:5555")
            
            print("\n📋 Useful commands:")
            print("   • View logs: docker-compose logs -f")
            print("   • Stop services: docker-compose down")
            print("   • Restart: docker-compose restart")
            
            return True
            
        except Exception as e:
            print(f"❌ Docker deployment failed: {e}")
            return False
    
    def deploy_aws(self) -> bool:
        """Deploy to AWS using Terraform"""
        print("☁️  Starting AWS deployment...")
        
        if not self.check_prerequisites('aws'):
            return False
        
        # Check AWS credentials
        try:
            subprocess.run(['aws', 'sts', 'get-caller-identity'], 
                         check=True, stdout=subprocess.DEVNULL)
            print("✅ AWS credentials configured")
        except subprocess.CalledProcessError:
            print("❌ AWS credentials not configured")
            print("💡 Run: aws configure")
            return False
        
        try:
            # Initialize Terraform
            print("🏗️  Initializing Terraform...")
            subprocess.run(['terraform', 'init'], 
                         cwd=self.terraform_dir, check=True)
            
            # Plan deployment
            print("📋 Planning deployment...")
            subprocess.run(['terraform', 'plan'], 
                         cwd=self.terraform_dir, check=True)
            
            # Apply deployment (with confirmation)
            confirm = input("\n❓ Apply Terraform changes? (yes/no): ")
            if confirm.lower() == 'yes':
                print("🚀 Applying Terraform configuration...")
                subprocess.run(['terraform', 'apply', '-auto-approve'], 
                             cwd=self.terraform_dir, check=True)
                print("✅ AWS deployment completed!")
            else:
                print("⏸️  Deployment cancelled")
                return False
            
            return True
            
        except Exception as e:
            print(f"❌ AWS deployment failed: {e}")
            return False
    
    def show_status(self, deployment_type: str):
        """Show status of deployment"""
        if deployment_type == 'docker':
            try:
                subprocess.run(['docker-compose', 'ps'])
            except:
                print("❌ Docker Compose not available or services not running")
        
        elif deployment_type == 'aws':
            try:
                subprocess.run(['terraform', 'output'], 
                             cwd=self.terraform_dir)
            except:
                print("❌ Terraform not initialized or no outputs available")
    
    def cleanup(self, deployment_type: str):
        """Clean up deployment"""
        if deployment_type == 'docker':
            print("🧹 Stopping Docker services...")
            subprocess.run(['docker-compose', 'down', '-v'])
            print("✅ Docker cleanup completed")
        
        elif deployment_type == 'aws':
            confirm = input("❗ This will destroy AWS resources. Continue? (yes/no): ")
            if confirm.lower() == 'yes':
                print("🧹 Destroying AWS resources...")
                subprocess.run(['terraform', 'destroy', '-auto-approve'], 
                             cwd=self.terraform_dir)
                print("✅ AWS cleanup completed")


def main():
    """Main deployment script entry point"""
    print("🎯 Enhanced Valuation Engine Deployment Manager")
    print("=" * 60)
    
    manager = DeploymentManager()
    
    if len(sys.argv) < 2:
        print("Usage: python deploy.py <command> [options]")
        print("\nCommands:")
        print("  local    - Deploy locally")
        print("  docker   - Deploy with Docker Compose")
        print("  aws      - Deploy to AWS with Terraform")
        print("  status   - Show deployment status")
        print("  cleanup  - Clean up deployment")
        print("\nExamples:")
        print("  python deploy.py docker")
        print("  python deploy.py status docker")
        print("  python deploy.py cleanup docker")
        return
    
    command = sys.argv[1].lower()
    deployment_type = sys.argv[2] if len(sys.argv) > 2 else None
    
    if command == 'local':
        success = manager.deploy_local()
    elif command == 'docker':
        success = manager.deploy_docker()
    elif command == 'aws':
        success = manager.deploy_aws()
    elif command == 'status' and deployment_type:
        manager.show_status(deployment_type)
        success = True
    elif command == 'cleanup' and deployment_type:
        manager.cleanup(deployment_type)
        success = True
    else:
        print(f"❌ Unknown command: {command}")
        success = False
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()