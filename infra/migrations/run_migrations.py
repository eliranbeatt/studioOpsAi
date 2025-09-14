#!/usr/bin/env python3
"""
Database migration runner for StudioOps AI
"""
import os
import psycopg2
import time
from pathlib import Path

def run_migrations():
    # Database connection parameters
    db_params = {
        'dbname': 'studioops',
        'user': 'studioops',
        'password': 'studioops123',
        'host': 'localhost',
        'port': '5432'
    }
    
    # Wait for PostgreSQL to be ready
    print("Waiting for PostgreSQL to be ready...")
    max_retries = 30
    retry_count = 0
    
    while retry_count < max_retries:
        try:
            conn = psycopg2.connect(**db_params)
            conn.close()
            print("PostgreSQL is ready!")
            break
        except psycopg2.OperationalError:
            retry_count += 1
            time.sleep(1)
            if retry_count % 5 == 0:
                print(f"Still waiting... ({retry_count}/{max_retries})")
    else:
        raise Exception("PostgreSQL not ready after 30 seconds")
    
    # Get migration files in order
    migration_dir = Path(__file__).parent
    migration_files = sorted([f for f in migration_dir.glob("*.sql") if f.name != "init.sql"])
    
    print(f"Found {len(migration_files)} migration files to apply")
    
    # Apply migrations
    conn = psycopg2.connect(**db_params)
    conn.autocommit = True
    cursor = conn.cursor()
    
    for migration_file in migration_files:
        print(f"Applying migration: {migration_file.name}")
        
        with open(migration_file, 'r', encoding='utf-8') as f:
            migration_sql = f.read()
        
        try:
            print(f"Executing SQL:\n{migration_sql}")
            cursor.execute(migration_sql)
            print(f"Finished executing SQL for {migration_file.name}")
            print(f"✓ Successfully applied {migration_file.name}")
        except Exception as e:
            print(f"✗ Failed to apply {migration_file.name}: {e}")
            raise
    
    cursor.close()
    conn.close()
    print("All migrations completed successfully!")

if __name__ == "__main__":
    run_migrations()