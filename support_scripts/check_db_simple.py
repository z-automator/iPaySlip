import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'payslip.settings')
django.setup()

from django.db import connection

# Check if tables exist
with connection.cursor() as cursor:
    cursor.execute("""
        SELECT table_name 
        FROM information_schema.tables 
        WHERE table_schema = 'public'
        ORDER BY table_name
    """)
    tables = cursor.fetchall()
    
    if tables:
        print(f"Found {len(tables)} tables:")
        for table in tables:
            print(f"  - {table[0]}")
    else:
        print("No tables found in the public schema.") 