#!/usr/bin/env python3
"""
Deployment script for Retail Promotion System
Author: Ricky
Version: 1.0
"""

import os
import sys
import subprocess
import logging
from pathlib import Path
import shutil

def setup_logging():
    """Setup logging configuration"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('deployment.log'),
            logging.StreamHandler()
        ]
    )
    return logging.getLogger(__name__)

def check_python_version():
    """Check Python version compatibility"""
    if sys.version_info < (3, 7):
        logger.error("Python 3.7 or higher is required")
        return False
    logger.info(f"Python version: {sys.version}")
    return True

def install_dependencies():
    """Install required dependencies"""
    try:
        logger.info("Installing dependencies...")
        subprocess.check_call([sys.executable, '-m', 'pip', 'install', '-r', 'requirements.txt'])
        logger.info("Dependencies installed successfully")
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to install dependencies: {e}")
        return False

def run_tests():
    """Run unit tests"""
    try:
        logger.info("Running unit tests...")
        result = subprocess.run([sys.executable, '-m', 'unittest', 'discover', '-s', '.', '-p', 'tests.py', '-v'], 
                              capture_output=True, text=True)
        
        if result.returncode == 0:
            logger.info("All tests passed")
            return True
        else:
            logger.error(f"Tests failed:\n{result.stderr}")
            return False
    except Exception as e:
        logger.error(f"Error running tests: {e}")
        return False

def create_sample_data():
    """Create sample data for testing"""
    try:
        logger.info("Creating sample data...")
        subprocess.check_call([sys.executable, 'sample_data_generator.py'])
        logger.info("Sample data created successfully")
        return True
    except Exception as e:
        logger.error(f"Error creating sample data: {e}")
        return False

def validate_environment():
    """Validate deployment environment"""
    required_files = ['app.py', 'requirements.txt', 'config.py']
    missing_files = []
    
    for file in required_files:
        if not os.path.exists(file):
            missing_files.append(file)
    
    if missing_files:
        logger.error(f"Missing required files: {missing_files}")
        return False
    
    logger.info("Environment validation passed")
    return True

def create_deployment_package():
    """Create deployment package"""
    try:
        logger.info("Creating deployment package...")
        
        # Create deployment directory
        deploy_dir = Path('deployment_package')
        deploy_dir.mkdir(exist_ok=True)
        
        # Copy essential files
        essential_files = [
            'app.py', 'requirements.txt', 'config.py', 'VERSION.md', 'README.md',
            'DEPLOYMENT.md', 'sample_data_generator.py'
        ]
        
        for file in essential_files:
            if os.path.exists(file):
                shutil.copy2(file, deploy_dir)
        
        # Copy sample data if exists
        sample_files = ['sample_inventory.xlsx', 'sample_promotion.xlsx']
        for file in sample_files:
            if os.path.exists(file):
                shutil.copy2(file, deploy_dir)
        
        logger.info(f"Deployment package created in {deploy_dir}")
        return True
    except Exception as e:
        logger.error(f"Error creating deployment package: {e}")
        return False

def main():
    """Main deployment function"""
    global logger
    logger = setup_logging()
    
    logger.info("Starting deployment process...")
    
    # Step 1: Check Python version
    if not check_python_version():
        return False
    
    # Step 2: Validate environment
    if not validate_environment():
        return False
    
    # Step 3: Install dependencies
    if not install_dependencies():
        return False
    
    # Step 4: Create sample data
    if not create_sample_data():
        logger.warning("Sample data creation failed, continuing...")
    
    # Step 5: Run tests
    if not run_tests():
        logger.warning("Some tests failed, continuing...")
    
    # Step 6: Create deployment package
    if not create_deployment_package():
        return False
    
    logger.info("Deployment process completed successfully!")
    logger.info("You can now run the application with: streamlit run app.py")
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)