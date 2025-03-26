import os
import sys
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'payslip.settings')
django.setup()

from django.db import connection
from django.core.management import call_command
from django.db.migrations.executor import MigrationExecutor
from django.db import connections

def force_migrate():
    # First check if we can connect to the database
    with connection.cursor() as cursor:
        cursor.execute("SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'public'")
        table_count = cursor.fetchone()[0]
        print(f"Current table count in public schema: {table_count}")
        
        # Clear the django_migrations table if it exists
        cursor.execute("""
            DROP TABLE IF EXISTS django_migrations CASCADE
        """)
        connection.commit()
        print("Dropped django_migrations table if it existed")
        
        # Drop all tables in the public schema to start fresh
        if table_count > 0:
            should_drop = input("Do you want to drop all existing tables? (y/n): ")
            if should_drop.lower() == 'y':
                cursor.execute("""
                    DO $$ DECLARE
                        r RECORD;
                    BEGIN
                        FOR r IN (SELECT tablename FROM pg_tables WHERE schemaname = 'public') LOOP
                            EXECUTE 'DROP TABLE IF EXISTS ' || quote_ident(r.tablename) || ' CASCADE';
                        END LOOP;
                    END $$;
                """)
                connection.commit()
                print("Dropped all tables in the public schema")
    
    # Force run migrations
    print("\nRunning migrations...")
    call_command('migrate', verbosity=1, interactive=False)
    
    # Verify migrations applied
    with connection.cursor() as cursor:
        cursor.execute("SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'public'")
        table_count = cursor.fetchone()[0]
        print(f"\nNew table count: {table_count}")
        
        if table_count > 0:
            cursor.execute("""
                SELECT table_name FROM information_schema.tables 
                WHERE table_schema = 'public'
                ORDER BY table_name
            """)
            tables = cursor.fetchall()
            print("Tables created:")
            for table in tables:
                print(f"  - {table[0]}")
        else:
            print("No tables were created.")

if __name__ == "__main__":
    force_migrate() 