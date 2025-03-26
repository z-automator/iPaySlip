import os
import sys
import django
from django.conf import settings

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'payslip.settings')
django.setup()

# Test database connection
from django.db import connection
try:
    connection.ensure_connection()
    print("Database connection successful!")
    print(f"Connected to: {connection.settings_dict['HOST']}:{connection.settings_dict['PORT']}")
    print(f"Database name: {connection.settings_dict['NAME']}")
    print(f"User: {connection.settings_dict['USER']}")
    
    # Check if we can execute a simple query
    with connection.cursor() as cursor:
        cursor.execute("SELECT 1")
        result = cursor.fetchone()
        print(f"Query result: {result}")
    
except Exception as e:
    print(f"Database connection failed!")
    print(f"Error type: {type(e).__name__}")
    print(f"Error message: {str(e)}")
    
    # Print connection settings (hiding password)
    conn_settings = connection.settings_dict.copy()
    if 'PASSWORD' in conn_settings:
        conn_settings['PASSWORD'] = '********'
    print(f"Connection settings: {conn_settings}")
    
    # Check if env variables are being read correctly
    import environ
    env = environ.Env()
    environ.Env.read_env()
    
    print("\nEnvironment variables:")
    print(f"DATABASE_NAME: {env('DATABASE_NAME', default='Not set')}")
    print(f"DATABASE_USER: {env('DATABASE_USER', default='Not set')}")
    print(f"DATABASE_HOST: {env('DATABASE_HOST', default='Not set')}")
    print(f"DATABASE_PORT: {env('DATABASE_PORT', default='Not set')}")
    print(f"DATABASE_SSL_MODE: {env('DATABASE_SSL_MODE', default='Not set')}") 