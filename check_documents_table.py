#!/usr/bin/env python3
"""
Check the documents table structure
"""

import psycopg2
import os
from dotenv import load_dotenv

load_dotenv()

def check_documents_table():
    """Check the documents table structure"""
    
    # Database connection parameters
    db_params = {
        'host': os.getenv('DB_HOST', 'localhost'),
        'port': os.getenv('DB_PORT', '5432'),
        'database': os.getenv('DB_NAME', 'studioops'),
        'user': os.getenv('DB_USER', 'studioops'),
        'password': os.getenv('DB_PASSWORD', 'studioops123')
    }
    
    try:
        conn = psycopg2.connect(**db_params)
        cursor = conn.cursor()
        
        # Check documents table columns
        cursor.execute("""
            SELECT column_name, data_type, is_nullable
            FROM information_schema.columns 
            WHERE table_name = 'documents' 
            AND table_schema = 'public'
            ORDER BY ordinal_position;
        """)
        
        columns = cursor.fetchall()
        print("📋 Documents table structure:")
        for column_name, data_type, is_nullable in columns:
            print(f"  - {column_name}: {data_type} (nullable: {is_nullable})")
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    check_documents_table()