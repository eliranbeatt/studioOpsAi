#!/usr/bin/env python3
"""
Add created_at column to vendor_prices table
"""

import psycopg2
import os
from dotenv import load_dotenv

load_dotenv()

def add_vendor_price_created_at():
    """Add created_at column to vendor_prices table"""
    try:
        conn = psycopg2.connect(
            os.getenv('DATABASE_URL', 'postgresql://studioops:studioops123@localhost:5432/studioops')
        )
        cursor = conn.cursor()
        
        # Check if column exists first
        cursor.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'vendor_prices' AND table_schema = 'public' AND column_name = 'created_at'
        """)
        existing_column = cursor.fetchone()
        
        if not existing_column:
            try:
                cursor.execute("ALTER TABLE vendor_prices ADD COLUMN created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()")
                print("✅ Added created_at column to vendor_prices table")
            except Exception as e:
                print(f"❌ Failed to add created_at column: {e}")
        else:
            print("⏭️  created_at column already exists in vendor_prices table")
        
        # Commit changes
        conn.commit()
        cursor.close()
        conn.close()
        
        print("✅ Successfully updated vendor_prices table")
        return True
        
    except Exception as e:
        print(f"❌ Error updating vendor_prices table: {e}")
        return False

if __name__ == "__main__":
    print("🔧 Adding created_at column to vendor_prices table")
    add_vendor_price_created_at()