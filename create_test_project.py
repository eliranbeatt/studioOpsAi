#!/usr/bin/env python3

import psycopg2
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv('apps/api/.env')

def create_test_project():
    try:
        conn = psycopg2.connect(
            os.getenv('DATABASE_URL', 'postgresql://studioops:studioops123@localhost:5432/studioops')
        )
        cursor = conn.cursor()
        
        # Create a test project
        cursor.execute("""
            INSERT INTO projects (name, client_name, status, start_date, due_date, budget_planned)
            VALUES (%s, %s, %s, %s, %s, %s)
            RETURNING id, name
        """, (
            "Test Project",
            "Test Client", 
            "active",
            "2025-01-01",
            "2025-12-31",
            100000.00
        ))
        
        project = cursor.fetchone()
        conn.commit()
        
        print(f"SUCCESS: Created test project!")
        print(f"Project ID: {project[0]}")
        print(f"Project Name: {project[1]}")
        
        # Verify the project exists
        cursor.execute("SELECT COUNT(*) FROM projects")
        count = cursor.fetchone()[0]
        print(f"Total projects in database: {count}")
        
        cursor.close()
        conn.close()
        return True
        
    except Exception as e:
        print(f"ERROR: Failed to create test project: {e}")
        return False

if __name__ == "__main__":
    create_test_project()