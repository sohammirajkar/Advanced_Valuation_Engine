#!/usr/bin/env python3
"""
Railway Deployment Helper Script
Provides utilities for managing Railway deployment.
"""

import os
import sys
import json
import subprocess
from pathlib import Path

class RailwayDeployer:
    """Helper class for Railway deployment operations"""
    
    def __init__(self):
        self.project_root = Path(__file__).parent.parent.parent
        
    def generate_railway_json(self, service_type: str) -> dict:
        """Generate Railway configuration JSON for a specific service"""
        
        base_config = {
            "$schema": "https://railway.com/railway.schema.json",
            "build": {
                "builder": "DOCKERFILE",
                "dockerfilePath": "Dockerfile"
            },
            "deploy": {
                "runtime": "V2",
                "restartPolicyType": "ON_FAILURE",
                "restartPolicyMaxRetries": 10
            }
        }
        
        if service_type == "frontend":
            base_config["deploy"]["startCommand"] = "python deployment/scripts/start_frontend.py"
        elif service_type == "backend":
            base_config["deploy"]["startCommand"] = "python deployment/scripts/start_backend.py"
        elif service_type == "worker":
            base_config["deploy"]["startCommand"] = "python deployment/scripts/start_worker.py"
        else:
            raise ValueError(f"Unknown service type: {service_type}")
            
        return base_config
    
    def create_railway_configs(self):
        """Create railway.json files for each service"""
        services = ["frontend", "backend", "worker"]
        
        for service in services:
            config = self.generate_railway_json(service)
            config_path = self.project_root / "deployment" / "configs" / f"railway-{service}.json"
            
            with open(config_path, 'w') as f:
                json.dump(config, f, indent=2)
            
            print(f"✅ Created {config_path}")
    
    def show_deployment_status(self):
        """Show current deployment file status"""
        print("📋 Deployment File Status")
        print("=" * 40)
        
        files_to_check = [
            "deployment/scripts/start_frontend.py",
            "deployment/scripts/start_backend.py", 
            "deployment/scripts/start_worker.py",
            "deployment/railway/services.yml",
            "deployment/railway/environment.yml",
            "Dockerfile",
            "requirements.txt"
        ]
        
        for file_path in files_to_check:
            full_path = self.project_root / file_path
            status = "✅" if full_path.exists() else "❌"
            print(f"{status} {file_path}")

def main():
    deployer = RailwayDeployer()
    
    if len(sys.argv) < 2:
        print("Usage: python deploy_helper.py <command>")
        print("Commands:")
        print("  status  - Show deployment file status")
        print("  config  - Generate Railway configuration files")
        return
    
    command = sys.argv[1]
    
    if command == "status":
        deployer.show_deployment_status()
    elif command == "config":
        deployer.create_railway_configs()
        print("\n📁 Configuration files created in deployment/configs/")
        print("Copy the appropriate railway-{service}.json to railway.json for each Railway service")
    else:
        print(f"Unknown command: {command}")

if __name__ == "__main__":
    main()