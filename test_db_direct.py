#!/usr/bin/env python3
"""
Direct database testing to check table structure
"""

import psycopg2
import os
from dotenv import load_dotenv

load_dotenv()

def test_db_connection():
    """Test direct database connection"""
    try:
        conn = psycopg2.connect(
            os.getenv('DATABASE_URL', 'postgresql://studioops:studioops123@localhost:5432/studioops')
        )
        cursor = conn.cursor()
        
        print("✅ Database connection successful")
        
        # Check if vendors table exists
        cursor.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public' 
            AND table_name IN ('vendors', 'materials', 'projects')
            ORDER BY table_name;
        """)
        
        tables = cursor.fetchall()
        print(f"Found tables: {[t[0] for t in tables]}")
        
        # Check vendors table structure
        if any(t[0] == 'vendors' for t in tables):
            cursor.execute("""
                SELECT column_name, data_type, is_nullable
                FROM information_schema.columns
                WHERE table_name = 'vendors'
                ORDER BY ordinal_position;
            """)
            
            columns = cursor.fetchall()
            print("\nVendors table structure:")
            for col in columns:
                print(f"  {col[0]}: {col[1]} ({'NULL' if col[2] == 'YES' else 'NOT NULL'})")
        
        # Try to query vendors table
        try:
            cursor.execute("SELECT COUNT(*) FROM vendors;")
            count = cursor.fetchone()[0]
            print(f"\nVendors table has {count} records")
        except Exception as e:
            print(f"❌ Error querying vendors table: {e}")
        
        # Check materials table
        if any(t[0] == 'materials' for t in tables):
            try:
                cursor.execute("SELECT COUNT(*) FROM materials;")
                count = cursor.fetchone()[0]
                print(f"Materials table has {count} records")
            except Exception as e:
                print(f"❌ Error querying materials table: {e}")
        
        # Check projects table
        if any(t[0] == 'projects' for t in tables):
            try:
                cursor.execute("SELECT COUNT(*) FROM projects;")
                count = cursor.fetchone()[0]
                print(f"Projects table has {count} records")
            except Exception as e:
                print(f"❌ Error querying projects table: {e}")
        
        cursor.close()
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        return False

if __name__ == "__main__":
    test_db_connection()