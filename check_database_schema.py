#!/usr/bin/env python3
"""
Check actual database schema to understand column names
"""

import psycopg2
from psycopg2.extras import RealDictCursor

DB_CONFIG = {
    'host': 'localhost',
    'port': 5432,
    'database': 'studioops',
    'user': 'studioops',
    'password': 'studioops123'
}

def check_schema():
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            # Get all tables
            cur.execute("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public' 
                ORDER BY table_name;
            """)
            tables = [row['table_name'] for row in cur.fetchall()]
            print(f"Found {len(tables)} tables: {tables}")
            
            # Check key tables
            key_tables = ['projects', 'vendors', 'materials', 'vendor_prices', 'purchases', 'chat_sessions', 'chat_messages']
            
            for table in key_tables:
                if table in tables:
                    print(f"\n=== {table.upper()} ===")
                    cur.execute(f"""
                        SELECT column_name, data_type, is_nullable, column_default
                        FROM information_schema.columns 
                        WHERE table_name = '{table}' 
                        ORDER BY ordinal_position;
                    """)
                    columns = cur.fetchall()
                    for col in columns:
                        print(f"  {col['column_name']}: {col['data_type']} {'NULL' if col['is_nullable'] == 'YES' else 'NOT NULL'}")
                else:
                    print(f"\n=== {table.upper()} === NOT FOUND")
        
        conn.close()
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    check_schema()