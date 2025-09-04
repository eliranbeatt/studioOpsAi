#!/usr/bin/env python3

import psycopg2
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv('apps/api/.env')

def run_migration():
    try:
        conn = psycopg2.connect(
            os.getenv('DATABASE_URL', 'postgresql://studioops:studioops123@localhost:5432/studioops')
        )
        cursor = conn.cursor()
        
        # Read the migration file
        with open('packages/db/migrations/001_initial_schema_no_vector.sql', 'r', encoding='utf-8') as f:
            migration_sql = f.read()
        
        # Execute the migration
        cursor.execute(migration_sql)
        conn.commit()
        
        print("SUCCESS: Database migration completed!")
        
        # Verify the projects table exists
        cursor.execute("SELECT COUNT(*) FROM projects")
        count = cursor.fetchone()[0]
        print(f"Projects table created with {count} rows")
        
        cursor.close()
        conn.close()
        return True
        
    except Exception as e:
        print(f"ERROR: Database migration failed: {e}")
        return False

if __name__ == "__main__":
    run_migration()