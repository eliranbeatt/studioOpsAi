#!/usr/bin/env python3
"""
Simple database migration runner for StudioOps AI
"""
import os
import psycopg2
from pathlib import Path

def run_migrations():
    """Run all database migrations in order"""
    
    # Get database connection string from environment
    database_url = os.getenv('DATABASE_URL', 'postgresql://studioops:studioops@localhost:5432/studioops')
    
    try:
        # Connect to database
        conn = psycopg2.connect(database_url)
        conn.autocommit = True
        cursor = conn.cursor()
        
        print("Connected to database successfully")
        
        # Create migrations table if it doesn't exist
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS schema_migrations (
                version INTEGER PRIMARY KEY,
                name TEXT NOT NULL,
                applied_at TIMESTAMPTZ DEFAULT NOW()
            )
        """)
        
        # Get all migration files
        migrations_dir = Path(__file__).parent / "migrations"
        migration_files = sorted(migrations_dir.glob("*.sql"))
        
        # Get applied migrations
        cursor.execute("SELECT version FROM schema_migrations ORDER BY version")
        applied_versions = {row[0] for row in cursor.fetchall()}
        
        # Run new migrations
        for migration_file in migration_files:
            version = int(migration_file.stem.split("_")[0])
            
            if version not in applied_versions:
                print(f"Running migration: {migration_file.name}")
                
                # Read and execute migration SQL
                with open(migration_file, 'r', encoding='utf-8') as f:
                    sql = f.read()
                
                # Execute migration
                cursor.execute(sql)
                
                # Record migration
                cursor.execute(
                    "INSERT INTO schema_migrations (version, name) VALUES (%s, %s)",
                    (version, migration_file.name)
                )
                
                print(f"✓ Applied migration {version}: {migration_file.name}")
        
        print("All migrations completed successfully")
        
    except Exception as e:
        print(f"Error running migrations: {e}")
        raise
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    run_migrations()