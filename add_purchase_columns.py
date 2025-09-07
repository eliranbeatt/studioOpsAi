#!/usr/bin/env python3
"""
Add missing columns to purchases table
"""

import psycopg2
import os
from dotenv import load_dotenv

load_dotenv()

def add_purchase_columns():
    """Add missing columns to purchases table"""
    try:
        conn = psycopg2.connect(
            os.getenv('DATABASE_URL', 'postgresql://studioops:studioops123@localhost:5432/studioops')
        )
        cursor = conn.cursor()
        
        # Check if columns exist first
        cursor.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'purchases' AND table_schema = 'public'
        """)
        existing_columns = [row[0] for row in cursor.fetchall()]
        print(f"Existing columns in purchases table: {existing_columns}")
        
        # Add missing columns
        columns_to_add = [
            ("sku", "VARCHAR"),
            ("unit", "VARCHAR"),
            ("total_nis", "NUMERIC(14,2)"),
            ("currency", "VARCHAR DEFAULT 'NIS'"),
            ("created_at", "TIMESTAMP WITH TIME ZONE DEFAULT NOW()")
        ]
        
        for column_name, column_type in columns_to_add:
            if column_name not in existing_columns:
                try:
                    cursor.execute(f"ALTER TABLE purchases ADD COLUMN {column_name} {column_type}")
                    print(f"✅ Added column: {column_name}")
                except Exception as e:
                    print(f"❌ Failed to add column {column_name}: {e}")
            else:
                print(f"⏭️  Column {column_name} already exists")
        
        # Commit changes
        conn.commit()
        cursor.close()
        conn.close()
        
        print("✅ Successfully updated purchases table")
        return True
        
    except Exception as e:
        print(f"❌ Error updating purchases table: {e}")
        return False

if __name__ == "__main__":
    print("🔧 Adding missing columns to purchases table")
    add_purchase_columns()