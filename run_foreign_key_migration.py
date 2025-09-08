#!/usr/bin/env python3
"""
Run the foreign key constraint migration
"""

import psycopg2
import os
from dotenv import load_dotenv

load_dotenv()

def run_foreign_key_migration():
    """Run the foreign key constraint migration"""
    
    # Database connection parameters
    db_params = {
        'host': os.getenv('DB_HOST', 'localhost'),
        'port': os.getenv('DB_PORT', '5432'),
        'database': os.getenv('DB_NAME', 'studioops'),
        'user': os.getenv('DB_USER', 'studioops'),
        'password': os.getenv('DB_PASSWORD', 'studioops123')
    }
    
    print("🔧 Running Foreign Key Constraint Migration")
    print("=" * 50)
    
    try:
        # Connect to database
        print(f"Connecting to database: {db_params['database']}@{db_params['host']}:{db_params['port']}")
        conn = psycopg2.connect(**db_params)
        conn.autocommit = True
        cursor = conn.cursor()
        
        # Read the migration file
        migration_file = "infra/migrations/004_fix_foreign_key_constraints.sql"
        print(f"Reading migration file: {migration_file}")
        
        with open(migration_file, 'r', encoding='utf-8') as f:
            migration_sql = f.read()
        
        # Execute the migration
        print("Executing migration...")
        cursor.execute(migration_sql)
        
        print("✅ Foreign key constraint migration completed successfully!")
        
        # Verify the constraints
        print("\n🔍 Verifying foreign key constraints...")
        
        verify_query = """
        SELECT 
            tc.table_name,
            tc.constraint_name,
            rc.delete_rule
        FROM information_schema.table_constraints tc
        JOIN information_schema.referential_constraints rc 
            ON tc.constraint_name = rc.constraint_name
        WHERE tc.constraint_type = 'FOREIGN KEY'
        AND tc.table_name IN ('chat_sessions', 'documents', 'purchases', 'plans', 'extracted_items', 'doc_chunks')
        AND rc.unique_constraint_name IN (
            SELECT constraint_name 
            FROM information_schema.table_constraints 
            WHERE table_name = 'projects' AND constraint_type = 'PRIMARY KEY'
        )
        ORDER BY tc.table_name;
        """
        
        cursor.execute(verify_query)
        constraints = cursor.fetchall()
        
        if constraints:
            print("Foreign key constraints found:")
            for table_name, constraint_name, delete_rule in constraints:
                print(f"  ✅ {table_name}: {constraint_name} (ON DELETE {delete_rule})")
        else:
            print("⚠️  No foreign key constraints found - this might indicate an issue")
        
        cursor.close()
        conn.close()
        
        return True
        
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        return False

if __name__ == "__main__":
    success = run_foreign_key_migration()
    if success:
        print("\n🎉 Migration completed successfully!")
        exit(0)
    else:
        print("\n💥 Migration failed!")
        exit(1)