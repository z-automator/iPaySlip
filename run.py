#!/usr/bin/env python
"""
Run script for the Payslip application.
This script provides a convenient way to run the application without Docker.
"""

import os
import sys
import subprocess
import argparse
import platform
from pathlib import Path

def check_core_dependencies():
    """Check if core dependencies are installed."""
    try:
        import django
        import psycopg2
        return True
    except ImportError as e:
        print(f"Missing core dependency: {e}")
        print("Please run: pip install -r requirements.txt")
        return False

def check_optional_dependencies():
    """Check if optional dependencies (Redis and Celery) are installed."""
    missing = []
    try:
        import redis
    except ImportError:
        missing.append('redis')
    
    try:
        import celery
    except ImportError:
        missing.append('celery')
    
    if missing:
        print("\nOptional dependencies not found:", ", ".join(missing))
        print("Some features like automated tasks and caching will be disabled.")
        print("To enable all features, install the missing packages:")
        print(f"pip install {' '.join(missing)}\n")
    
    return len(missing) == 0

def setup_environment():
    """Set up the environment variables."""
    if not os.path.exists('.env'):
        if os.path.exists('.env.example'):
            print("Creating .env file from .env.example...")
            with open('.env.example', 'r') as example, open('.env', 'w') as env:
                env.write(example.read())
            print("Please update the .env file with your settings.")
            return False
        else:
            print("No .env or .env.example file found!")
            return False
    return True

def run_development():
    """Run the application in development mode."""
    if not check_core_dependencies():
        return

    # Check optional dependencies but don't block execution
    has_optional_deps = check_optional_dependencies()

    # Create logs directory if it doesn't exist
    Path('logs').mkdir(exist_ok=True)

    if not setup_environment():
        return

    # Run migrations
    print("Running migrations...")
    subprocess.run([sys.executable, 'manage.py', 'migrate'])

    # Collect static files
    print("Collecting static files...")
    subprocess.run([sys.executable, 'manage.py', 'collectstatic', '--noinput'])

    # Start development server
    print("\nStarting development server...")
    subprocess.run([sys.executable, 'manage.py', 'runserver'])

def run_production():
    """Run the application in production mode."""
    if not check_core_dependencies():
        return

    # In production, we should warn about missing optional dependencies
    if not check_optional_dependencies():
        print("\nWARNING: Running in production without Redis/Celery is not recommended.")
        response = input("Do you want to continue anyway? (y/N): ")
        if response.lower() != 'y':
            print("Aborted. Please install Redis and Celery for production use.")
            return

    # Create logs directory if it doesn't exist
    Path('logs').mkdir(exist_ok=True)

    if not setup_environment():
        return

    # Set production settings
    os.environ['DJANGO_SETTINGS_MODULE'] = 'payslip.settings_prod'

    # Run migrations
    print("Running migrations...")
    subprocess.run([sys.executable, 'manage.py', 'migrate'])

    # Collect static files
    print("Collecting static files...")
    subprocess.run([sys.executable, 'manage.py', 'collectstatic', '--noinput'])

    # Check if we're on Windows
    if platform.system() == 'Windows':
        try:
            import waitress
        except ImportError:
            print("Installing waitress...")
            subprocess.run([sys.executable, '-m', 'pip', 'install', 'waitress'])
            import waitress

        print("\nStarting production server with Waitress...")
        from waitress import serve
        from payslip.wsgi_prod import application
        serve(application, host='0.0.0.0', port=8000, threads=4)
    else:
        try:
            # Check if gunicorn is installed
            import gunicorn
        except ImportError:
            print("Installing gunicorn...")
            subprocess.run([sys.executable, '-m', 'pip', 'install', 'gunicorn'])

        # Start Gunicorn
        print("\nStarting production server with Gunicorn...")
        subprocess.run([
            'gunicorn',
            'payslip.wsgi_prod:application',
            '--bind', '0.0.0.0:8000',
            '--workers', '3',
            '--timeout', '120',
            '--access-logfile', 'logs/access.log',
            '--error-logfile', 'logs/error.log'
        ])

def main():
    parser = argparse.ArgumentParser(description='Run the Payslip application.')
    parser.add_argument(
        '--env',
        choices=['dev', 'prod'],
        default='dev',
        help='Environment to run the application in (default: dev)'
    )
    args = parser.parse_args()

    if args.env == 'dev':
        run_development()
    else:
        run_production()

if __name__ == '__main__':
    main() 