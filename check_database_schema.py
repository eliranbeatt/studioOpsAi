#!/usr/bin/env python3
"""
Check the current database schema to understand data types and constraints
"""

import psycopg2
import os
from dotenv import load_dotenv

load_dotenv()

def check_database_schema():
    """Check the current database schema"""
    
    # Database connection parameters
    db_params = {
        'host': os.getenv('DB_HOST', 'localhost'),
        'port': os.getenv('DB_PORT', '5432'),
        'database': os.getenv('DB_NAME', 'studioops'),
        'user': os.getenv('DB_USER', 'studioops'),
        'password': os.getenv('DB_PASSWORD', 'studioops123')
    }
    
    print("🔍 Checking Database Schema")
    print("=" * 50)
    
    try:
        # Connect to database
        conn = psycopg2.connect(**db_params)
        cursor = conn.cursor()
        
        # Check which tables exist
        print("📋 Existing tables:")
        cursor.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public' 
            ORDER BY table_name;
        """)
        tables = cursor.fetchall()
        for table in tables:
            print(f"  - {table[0]}")
        
        # Check data types for project_id columns
        print("\n🔗 Project ID column data types:")
        cursor.execute("""
            SELECT 
                table_name, 
                column_name, 
                data_type,
                is_nullable
            FROM information_schema.columns 
            WHERE column_name = 'project_id' 
            AND table_schema = 'public'
            ORDER BY table_name;
        """)
        project_id_columns = cursor.fetchall()
        for table_name, column_name, data_type, is_nullable in project_id_columns:
            print(f"  - {table_name}.{column_name}: {data_type} (nullable: {is_nullable})")
        
        # Check projects table primary key type
        print("\n🔑 Projects table primary key:")
        cursor.execute("""
            SELECT 
                column_name, 
                data_type
            FROM information_schema.columns 
            WHERE table_name = 'projects' 
            AND column_name = 'id'
            AND table_schema = 'public';
        """)
        projects_pk = cursor.fetchone()
        if projects_pk:
            print(f"  - projects.id: {projects_pk[1]}")
        else:
            print("  - projects table not found or no id column")
        
        # Check existing foreign key constraints
        print("\n🔗 Existing foreign key constraints:")
        cursor.execute("""
            SELECT 
                tc.table_name,
                tc.constraint_name,
                kcu.column_name,
                ccu.table_name AS foreign_table_name,
                ccu.column_name AS foreign_column_name,
                rc.delete_rule
            FROM information_schema.table_constraints tc
            JOIN information_schema.key_column_usage kcu 
                ON tc.constraint_name = kcu.constraint_name
            JOIN information_schema.constraint_column_usage ccu 
                ON ccu.constraint_name = tc.constraint_name
            JOIN information_schema.referential_constraints rc 
                ON tc.constraint_name = rc.constraint_name
            WHERE tc.constraint_type = 'FOREIGN KEY'
            AND (tc.table_name IN ('chat_sessions', 'documents', 'purchases', 'plans', 'extracted_items', 'doc_chunks')
                 OR ccu.table_name = 'projects')
            ORDER BY tc.table_name;
        """)
        constraints = cursor.fetchall()
        
        if constraints:
            for table_name, constraint_name, column_name, foreign_table, foreign_column, delete_rule in constraints:
                print(f"  - {table_name}.{column_name} -> {foreign_table}.{foreign_column} (ON DELETE {delete_rule})")
        else:
            print("  - No foreign key constraints found")
        
        cursor.close()
        conn.close()
        
        return True
        
    except Exception as e:
        print(f"❌ Schema check failed: {e}")
        return False

if __name__ == "__main__":
    check_database_schema()