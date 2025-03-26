import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'payslip.settings')
django.setup()

from django.db import connection

# Check which database we're connecting to
with connection.cursor() as cursor:
    cursor.execute('SELECT current_database()')
    db_name = cursor.fetchone()[0]
    print(f"Connected to database: {db_name}")
    
    # Check if tables exist
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
        
    # Check connection parameters
    cursor.execute("SHOW search_path;")
    search_path = cursor.fetchone()[0]
    print(f"Search path: {search_path}")
    
    # Print connection info
    print("\nConnection details:")
    for key, value in connection.get_connection_params().items():
        if key != 'password':  # Don't print the password
            print(f"  {key}: {value}") 