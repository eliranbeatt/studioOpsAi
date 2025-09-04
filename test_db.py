#!/usr/bin/env python3

import psycopg2
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv('apps/api/.env')

def test_db_connection():
    try:
        conn = psycopg2.connect(
            os.getenv('DATABASE_URL', 'postgresql://studioops:studioops123@localhost:5432/studioops')
        )
        cursor = conn.cursor()
        cursor.execute("SELECT 1")
        result = cursor.fetchone()
        print("SUCCESS: Database connection successful!")
        print(f"Result: {result}")
        
        # Test projects table
        cursor.execute("SELECT COUNT(*) FROM projects")
        count = cursor.fetchone()[0]
        print(f"Projects in database: {count}")
        
        cursor.close()
        conn.close()
        return True
        
    except Exception as e:
        print(f"ERROR: Database connection failed: {e}")
        return False

if __name__ == "__main__":
    test_db_connection()