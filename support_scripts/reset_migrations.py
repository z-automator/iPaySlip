import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'payslip.settings')
django.setup()

from django.db import connection

def reset_migrations():
    with connection.cursor() as cursor:
        # Check if django_migrations table exists
        cursor.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public' 
            AND table_name = 'django_migrations'
        """)
        
        if cursor.fetchone():
            print("django_migrations table exists.")
            cursor.execute("DELETE FROM django_migrations")
            connection.commit()
            print("Migration records deleted")
        else:
            print("django_migrations table doesn't exist. Creating it...")
            cursor.execute('''
            CREATE TABLE django_migrations (
                id serial NOT NULL PRIMARY KEY,
                app varchar(255) NOT NULL,
                name varchar(255) NOT NULL,
                applied timestamp with time zone NOT NULL
            )''')
            connection.commit()
            print("django_migrations table created")
            
        print("\nMigration state has been reset. Now run:")
        print("python manage.py migrate")

if __name__ == "__main__":
    reset_migrations() 