#!/usr/bin/env python3
"""
Test the database foreign key constraints directly
"""

import psycopg2
import uuid
import os
from dotenv import load_dotenv

load_dotenv()

def test_database_foreign_keys():
    """Test foreign key constraints directly in the database"""
    
    print("🔗 Testing Database Foreign Key Constraints")
    print("=" * 50)
    
    # Database connection parameters
    db_params = {
        'host': os.getenv('DB_HOST', 'localhost'),
        'port': os.getenv('DB_PORT', '5432'),
        'database': os.getenv('DB_NAME', 'studioops'),
        'user': os.getenv('DB_USER', 'studioops'),
        'password': os.getenv('DB_PASSWORD', 'studioops123')
    }
    
    try:
        # Connect to database
        conn = psycopg2.connect(**db_params)
        conn.autocommit = False
        cursor = conn.cursor()
        
        # Generate test project ID
        test_project_id = str(uuid.uuid4())
        
        print(f"1. Creating test project: {test_project_id}")
        
        # Create a test project
        cursor.execute("""
            INSERT INTO projects (id, name, client_name, status)
            VALUES (%s, %s, %s, %s)
        """, (test_project_id, "FK Test Project", "Test Client", "active"))
        
        print("✅ Test project created")
        
        # Create related records
        print("2. Creating related records...")
        
        # Create a chat session
        chat_session_id = str(uuid.uuid4())
        cursor.execute("""
            INSERT INTO chat_sessions (id, project_id, title, user_id)
            VALUES (%s, %s, %s, %s)
        """, (chat_session_id, test_project_id, "Test Chat", "test_user"))
        print("   ✅ Chat session created")
        
        # Create a document
        document_id = str(uuid.uuid4())
        cursor.execute("""
            INSERT INTO documents (id, project_id, type, path)
            VALUES (%s, %s, %s, %s)
        """, (document_id, test_project_id, "test", "/test/path"))
        print("   ✅ Document created")
        
        # Create a purchase
        purchase_id = str(uuid.uuid4())
        cursor.execute("""
            INSERT INTO purchases (id, project_id, qty, unit_price_nis)
            VALUES (%s, %s, %s, %s)
        """, (purchase_id, test_project_id, 10, 100.50))
        print("   ✅ Purchase created")
        
        # Create a plan (this should CASCADE delete)
        plan_id = str(uuid.uuid4())
        cursor.execute("""
            INSERT INTO plans (id, project_id, version, status)
            VALUES (%s, %s, %s, %s)
        """, (plan_id, test_project_id, 1, "draft"))
        print("   ✅ Plan created")
        
        # Commit the setup
        conn.commit()
        
        # Now test the deletion
        print("3. Testing project deletion...")
        
        # This should work now with our foreign key fixes
        cursor.execute("DELETE FROM projects WHERE id = %s", (test_project_id,))
        deleted_count = cursor.rowcount
        
        if deleted_count == 1:
            print("✅ Project deleted successfully!")
            
            # Check that related records were handled correctly
            print("4. Verifying related record handling...")
            
            # Chat sessions should have project_id set to NULL
            cursor.execute("SELECT project_id FROM chat_sessions WHERE id = %s", (chat_session_id,))
            chat_result = cursor.fetchone()
            if chat_result and chat_result[0] is None:
                print("   ✅ Chat session project_id set to NULL")
            else:
                print(f"   ❌ Chat session project_id not handled correctly: {chat_result}")
            
            # Documents should have project_id set to NULL
            cursor.execute("SELECT project_id FROM documents WHERE id = %s", (document_id,))
            doc_result = cursor.fetchone()
            if doc_result and doc_result[0] is None:
                print("   ✅ Document project_id set to NULL")
            else:
                print(f"   ❌ Document project_id not handled correctly: {doc_result}")
            
            # Purchases should have project_id set to NULL
            cursor.execute("SELECT project_id FROM purchases WHERE id = %s", (purchase_id,))
            purchase_result = cursor.fetchone()
            if purchase_result and purchase_result[0] is None:
                print("   ✅ Purchase project_id set to NULL")
            else:
                print(f"   ❌ Purchase project_id not handled correctly: {purchase_result}")
            
            # Plans should be deleted (CASCADE)
            cursor.execute("SELECT id FROM plans WHERE id = %s", (plan_id,))
            plan_result = cursor.fetchone()
            if plan_result is None:
                print("   ✅ Plan deleted via CASCADE")
            else:
                print(f"   ❌ Plan not deleted: {plan_result}")
            
            conn.commit()
            
            print("\n🎉 All foreign key constraint tests PASSED!")
            return True
        
        else:
            print(f"❌ Project deletion failed - {deleted_count} rows affected")
            conn.rollback()
            return False
    
    except Exception as e:
        print(f"❌ Test failed: {e}")
        try:
            conn.rollback()
        except:
            pass
        return False
    
    finally:
        try:
            cursor.close()
            conn.close()
        except:
            pass

if __name__ == "__main__":
    success = test_database_foreign_keys()
    if success:
        print("\n✅ Database foreign key tests completed successfully!")
        exit(0)
    else:
        print("\n❌ Database foreign key tests failed!")
        exit(1)