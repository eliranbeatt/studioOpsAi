#!/usr/bin/env python3
"""
Initialize authentication schema and create default admin user
"""

import os
import sys
import psycopg2
from passlib.context import CryptContext
from uuid import uuid4

# Add the parent directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def get_db_connection():
    """Get database connection"""
    return psycopg2.connect(
        os.getenv('DATABASE_URL', 'postgresql://studioops:studioops@localhost:5432/studioops')
    )

def init_auth_schema():
    """Initialize authentication schema"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # Read and execute the auth schema SQL
        auth_schema_path = os.path.join(os.path.dirname(__file__), '..', '..', 'infra', 'auth-schema.sql')
        with open(auth_schema_path, 'r', encoding='utf-8') as f:
            schema_sql = f.read()
        
        cursor.execute(schema_sql)
        print("✓ Authentication schema initialized")
        
        # Create default admin user if it doesn't exist
        cursor.execute("SELECT id FROM users WHERE email = 'admin@studioops.ai'")
        if not cursor.fetchone():
            hashed_password = pwd_context.hash("admin123")
            cursor.execute(
                """INSERT INTO users (id, email, full_name, hashed_password, is_superuser)
                   VALUES (%s, %s, %s, %s, %s)""",
                (str(uuid4()), 'admin@studioops.ai', 'System Administrator', hashed_password, True)
            )
            print("✓ Default admin user created (admin@studioops.ai / admin123)")
        
        conn.commit()
        print("✓ Authentication setup completed successfully")
        
    except Exception as e:
        conn.rollback()
        print(f"✗ Error initializing auth schema: {e}")
        raise
    finally:
        cursor.close()
        conn.close()

if __name__ == "__main__":
    print("Initializing authentication schema...")
    init_auth_schema()