#!/usr/bin/env python3
"""Check plans table schema"""

import psycopg2
import os
from dotenv import load_dotenv

load_dotenv()

def check_plans_schema():
    conn = psycopg2.connect(
        host=os.getenv('DB_HOST', 'localhost'),
        port=os.getenv('DB_PORT', '5432'),
        database=os.getenv('DB_NAME', 'studioops'),
        user=os.getenv('DB_USER', 'studioops'),
        password=os.getenv('DB_PASSWORD', 'studioops123')
    )

    cursor = conn.cursor()
    
    # Check plans table schema
    cursor.execute("""
        SELECT column_name, data_type, is_nullable 
        FROM information_schema.columns 
        WHERE table_name = 'plans' 
        ORDER BY ordinal_position
    """)

    print('Plans table columns:')
    for row in cursor.fetchall():
        print(f'  - {row[0]}: {row[1]} (nullable: {row[2]})')

    # Check project_id column specifically
    cursor.execute("""
        SELECT data_type 
        FROM information_schema.columns 
        WHERE table_name = 'plans' AND column_name = 'project_id'
    """)

    result = cursor.fetchone()
    if result:
        print(f'\nPlans.project_id column type: {result[0]}')
    else:
        print('\nNo project_id column found in plans table')

    cursor.close()
    conn.close()

if __name__ == "__main__":
    check_plans_schema()