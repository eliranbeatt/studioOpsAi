#!/usr/bin/env python3

import psycopg2
import os
from dotenv import load_dotenv
import json

# Load environment variables
load_dotenv('apps/api/.env')

def test_project_workflow():
    """Test the complete project management workflow"""
    
    print("=== StudioOps AI Project Management Workflow Test ===\n")
    
    try:
        # Connect to database
        conn = psycopg2.connect(
            os.getenv('DATABASE_URL', 'postgresql://studioops:studioops123@localhost:5432/studioops')
        )
        cursor = conn.cursor()
        
        print("[OK] Database connection successful")
        
        # 1. Check current projects
        cursor.execute("SELECT COUNT(*) FROM projects")
        initial_count = cursor.fetchone()[0]
        print(f"📊 Initial projects count: {initial_count}")
        
        # 2. Create a new project
        print("\n➕ Creating a new project...")
        cursor.execute("""
            INSERT INTO projects (name, client_name, status, start_date, due_date, budget_planned)
            VALUES (%s, %s, %s, %s, %s, %s)
            RETURNING id, name, client_name, status, start_date, due_date, budget_planned
        """, (
            "Website Redesign",
            "Acme Corp",
            "active",
            "2025-01-15",
            "2025-06-30",
            50000.00
        ))
        
        project = cursor.fetchone()
        conn.commit()
        
        print(f"[OK] Project created successfully!")
        print(f"   ID: {project[0]}")
        print(f"   Name: {project[1]}")
        print(f"   Client: {project[2]}")
        print(f"   Status: {project[3]}")
        print(f"   Budget: ₪{project[6]:,.2f}")
        
        # 3. Verify project was saved
        cursor.execute("SELECT COUNT(*) FROM projects")
        new_count = cursor.fetchone()[0]
        print(f"\n📊 New projects count: {new_count}")
        
        if new_count == initial_count + 1:
            print("✅ Project persistence verified!")
        else:
            print("❌ Project persistence failed!")
            return False
        
        # 4. Retrieve all projects
        print("\n📋 Retrieving all projects...")
        cursor.execute("""
            SELECT id, name, client_name, status, start_date, due_date, budget_planned, created_at
            FROM projects ORDER BY created_at DESC
        """)
        
        projects = cursor.fetchall()
        print(f"Found {len(projects)} projects:")
        
        for i, project in enumerate(projects, 1):
            print(f"  {i}. {project[1]} ({project[2]}) - {project[3]} - ₪{project[6] or 0:,.2f}")
        
        # 5. Test project update
        print(f"\n✏️  Updating project status...")
        cursor.execute("""
            UPDATE projects SET status = %s, budget_planned = %s
            WHERE id = %s
            RETURNING id, name, status, budget_planned
        """, (
            "completed",
            55000.00,  # Updated budget
            project[0]  # Use the ID from the created project
        ))
        
        updated_project = cursor.fetchone()
        conn.commit()
        
        print(f"✅ Project updated successfully!")
        print(f"   Name: {updated_project[1]}")
        print(f"   New Status: {updated_project[2]}")
        print(f"   New Budget: ₪{updated_project[3]:,.2f}")
        
        # 6. Test project deletion
        print(f"\n🗑️  Testing project deletion...")
        cursor.execute("DELETE FROM projects WHERE id = %s RETURNING id", (project[0],))
        
        deleted_id = cursor.fetchone()
        conn.commit()
        
        if deleted_id:
            print(f"✅ Project deleted successfully!")
            print(f"   Deleted Project ID: {deleted_id[0]}")
        else:
            print("❌ Project deletion failed!")
            return False
        
        # 7. Final verification
        cursor.execute("SELECT COUNT(*) FROM projects")
        final_count = cursor.fetchone()[0]
        print(f"\n📊 Final projects count: {final_count}")
        
        if final_count == initial_count:
            print("✅ All tests passed! Project management workflow is fully functional!")
        else:
            print("❌ Test failed: Project count mismatch")
            return False
        
        cursor.close()
        conn.close()
        
        print("\n🎉 SUCCESS: Project management database operations are working perfectly!")
        print("\nThe system is ready for:")
        print("  • Creating new projects")
        print("  • Reading project data") 
        print("  • Updating project information")
        print("  • Deleting projects")
        print("  • Persistent storage in PostgreSQL")
        
        return True
        
    except Exception as e:
        print(f"❌ ERROR: {e}")
        return False

if __name__ == "__main__":
    success = test_project_workflow()
    exit(0 if success else 1)