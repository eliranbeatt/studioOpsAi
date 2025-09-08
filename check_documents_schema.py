#!/usr/bin/env python3
"""Check documents table schema"""

import psycopg2
import os
from dotenv import load_dotenv

load_dotenv()

def check_documents_schema():
    conn = psycopg2.connect(
        host=os.getenv('DB_HOST', 'localhost'),
        port=os.getenv('DB_PORT', '5432'),
        database=os.getenv('DB_NAME', 'studioops'),
        user=os.getenv('DB_USER', 'studioops'),
        password=os.getenv('DB_PASSWORD', 'studioops123')
    )

    cursor = conn.cursor()
    cursor.execute("""
        SELECT column_name, data_type, is_nullable 
        FROM information_schema.columns 
        WHERE table_name = 'documents' 
        ORDER BY ordinal_position
    """)

    print('Documents table columns:')
    for row in cursor.fetchall():
        print(f'  - {row[0]}: {row[1]} (nullable: {row[2]})')

    cursor.close()
    conn.close()

if __name__ == "__main__":
    check_documents_schema()