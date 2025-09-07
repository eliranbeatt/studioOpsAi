#!/usr/bin/env python3
"""
Fix existing data with NULL updated_at values
"""

import psycopg2
from datetime import datetime
import os
from dotenv import load_dotenv

load_dotenv()

def fix_null_updated_at():
    """Fix NULL updated_at values in vendors and materials tables"""
    try:
        conn = psycopg2.connect(
            os.getenv('DATABASE_URL', 'postgresql://studioops:studioops123@localhost:5432/studioops')
        )
        cursor = conn.cursor()
        
        # Fix vendors table
        cursor.execute("""
            UPDATE vendors 
            SET updated_at = created_at 
            WHERE updated_at IS NULL
        """)
        vendors_updated = cursor.rowcount
        print(f"Updated {vendors_updated} vendors with NULL updated_at")
        
        # Fix materials table
        cursor.execute("""
            UPDATE materials 
            SET updated_at = created_at 
            WHERE updated_at IS NULL
        """)
        materials_updated = cursor.rowcount
        print(f"Updated {materials_updated} materials with NULL updated_at")
        
        # Commit changes
        conn.commit()
        cursor.close()
        conn.close()
        
        print("✅ Successfully fixed NULL updated_at values")
        return True
        
    except Exception as e:
        print(f"❌ Error fixing data: {e}")
        return False

if __name__ == "__main__":
    print("🔧 Fixing existing data with NULL updated_at values")
    fix_null_updated_at()