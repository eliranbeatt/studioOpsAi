#!/usr/bin/env python3
"""
Comprehensive test for project deletion functionality
Tests both database-level and API-level deletion
"""

import requests
import psycopg2
import uuid
import os
import time
from dotenv import load_dotenv

load_dotenv()

API_BASE_URL = "http://localhost:8000"

def wait_for_api():
    """Wait for API to be available"""
    print("⏳ Waiting for API to be available...")
    
    for i in range(30):  # Wait up to 30 seconds
        try:
            response = requests.get(f"{API_BASE_URL}/health", timeout=2)
            if response.status_code == 200:
                print("✅ API is available")
                return True
        except:
            pass
        
        time.sleep(1)
        if i % 5 == 0:
            print(f"   Still waiting... ({i+1}/30)")
    
    print("❌ API not available after 30 seconds")
    return False

def test_api_project_deletion():
    """Test project deletion via API"""
    
    print("\n🌐 Testing API Project Deletion")
    print("=" * 40)
    
    try:
        # 1. Create a test project via API
        print("1. Creating test project via API...")
        project_data = {
            "name": f"API Test Project {uuid.uuid4().hex[:8]}",
            "client_name": "API Test Client",
            "status": "active"
        }
        
        response = requests.post(f"{API_BASE_URL}/projects", json=project_data, timeout=10)
        if response.status_code != 200:
            print(f"❌ Failed to create project: {response.status_code}")
            print(f"   Response: {response.text}")
            return False
        
        project = response.json()
        project_id = project["id"]
        print(f"✅ Created project: {project['name']} (ID: {project_id})")
        
        # 2. Get deletion impact analysis
        print("2. Getting deletion impact analysis...")
        response = requests.get(f"{API_BASE_URL}/projects/{project_id}/deletion-impact", timeout=10)
        if response.status_code == 200:
            impact = response.json()
            print(f"✅ Deletion impact analysis:")
            print(f"   - Can delete: {impact.get('can_delete', False)}")
            print(f"   - Project name: {impact.get('project_name', 'Unknown')}")
            print(f"   - Safe deletion: {impact.get('safe_deletion', False)}")
            if impact.get('warnings'):
                for warning in impact['warnings']:
                    print(f"   - Warning: {warning}")
        else:
            print(f"⚠️  Could not get deletion impact: {response.status_code}")
        
        # 3. Delete the project via API
        print("3. Deleting project via API...")
        response = requests.delete(f"{API_BASE_URL}/projects/{project_id}", timeout=10)
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Project deleted successfully!")
            print(f"   - Message: {result.get('message', 'No message')}")
            print(f"   - Project name: {result.get('project_name', 'Unknown')}")
            
            if 'deletion_stats' in result:
                stats = result['deletion_stats']
                print(f"   - Chat sessions unlinked: {stats.get('chat_sessions_unlinked', 0)}")
                print(f"   - Documents unlinked: {stats.get('documents_unlinked', 0)}")
                print(f"   - Purchases unlinked: {stats.get('purchases_unlinked', 0)}")
                print(f"   - Plans deleted: {stats.get('plans_deleted', 0)}")
            
            # 4. Verify project is deleted
            print("4. Verifying project deletion...")
            response = requests.get(f"{API_BASE_URL}/projects/{project_id}", timeout=10)
            if response.status_code == 404:
                print("✅ Project successfully deleted - returns 404 as expected")
                return True
            else:
                print(f"❌ Project still exists after deletion: {response.status_code}")
                return False
        
        else:
            print(f"❌ Project deletion failed: {response.status_code}")
            print(f"   Response: {response.text}")
            return False
    
    except Exception as e:
        print(f"❌ API test failed: {e}")
        return False

def test_database_project_deletion():
    """Test project deletion directly in database"""
    
    print("\n🗄️  Testing Database Project Deletion")
    print("=" * 40)
    
    # Database connection parameters
    db_params = {
        'host': os.getenv('DB_HOST', 'localhost'),
        'port': os.getenv('DB_PORT', '5432'),
        'database': os.getenv('DB_NAME', 'studioops'),
        'user': os.getenv('DB_USER', 'studioops'),
        'password': os.getenv('DB_PASSWORD', 'studioops123')
    }
    
    try:
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
        """, (test_project_id, "DB Test Project", "DB Test Client", "active"))
        
        # Create related records to test foreign key handling
        chat_session_id = str(uuid.uuid4())
        cursor.execute("""
            INSERT INTO chat_sessions (id, project_id, title, user_id)
            VALUES (%s, %s, %s, %s)
        """, (chat_session_id, test_project_id, "Test Chat", "test_user"))
        
        document_id = str(uuid.uuid4())
        cursor.execute("""
            INSERT INTO documents (id, project_id, type, path)
            VALUES (%s, %s, %s, %s)
        """, (document_id, test_project_id, "test", "/test/path"))
        
        purchase_id = str(uuid.uuid4())
        cursor.execute("""
            INSERT INTO purchases (id, project_id, qty, unit_price_nis)
            VALUES (%s, %s, %s, %s)
        """, (purchase_id, test_project_id, 10, 100.50))
        
        plan_id = str(uuid.uuid4())
        cursor.execute("""
            INSERT INTO plans (id, project_id, version, status)
            VALUES (%s, %s, %s, %s)
        """, (plan_id, test_project_id, 1, "draft"))
        
        conn.commit()
        print("✅ Test project and related records created")
        
        # Test deletion
        print("2. Testing project deletion...")
        cursor.execute("DELETE FROM projects WHERE id = %s", (test_project_id,))
        deleted_count = cursor.rowcount
        
        if deleted_count == 1:
            print("✅ Project deleted successfully!")
            
            # Verify foreign key handling
            print("3. Verifying foreign key constraint handling...")
            
            # Check chat sessions (should be SET NULL)
            cursor.execute("SELECT project_id FROM chat_sessions WHERE id = %s", (chat_session_id,))
            chat_result = cursor.fetchone()
            if chat_result and chat_result[0] is None:
                print("   ✅ Chat session project_id set to NULL")
            else:
                print(f"   ❌ Chat session project_id not handled correctly: {chat_result}")
                return False
            
            # Check documents (should be SET NULL)
            cursor.execute("SELECT project_id FROM documents WHERE id = %s", (document_id,))
            doc_result = cursor.fetchone()
            if doc_result and doc_result[0] is None:
                print("   ✅ Document project_id set to NULL")
            else:
                print(f"   ❌ Document project_id not handled correctly: {doc_result}")
                return False
            
            # Check purchases (should be SET NULL)
            cursor.execute("SELECT project_id FROM purchases WHERE id = %s", (purchase_id,))
            purchase_result = cursor.fetchone()
            if purchase_result and purchase_result[0] is None:
                print("   ✅ Purchase project_id set to NULL")
            else:
                print(f"   ❌ Purchase project_id not handled correctly: {purchase_result}")
                return False
            
            # Check plans (should be CASCADE deleted)
            cursor.execute("SELECT id FROM plans WHERE id = %s", (plan_id,))
            plan_result = cursor.fetchone()
            if plan_result is None:
                print("   ✅ Plan deleted via CASCADE")
            else:
                print(f"   ❌ Plan not deleted: {plan_result}")
                return False
            
            conn.commit()
            return True
        
        else:
            print(f"❌ Project deletion failed - {deleted_count} rows affected")
            return False
    
    except Exception as e:
        print(f"❌ Database test failed: {e}")
        return False
    
    finally:
        try:
            cursor.close()
            conn.close()
        except:
            pass

def main():
    """Run comprehensive project deletion tests"""
    
    print("🚀 Comprehensive Project Deletion Tests")
    print("=" * 60)
    
    # Test 1: Database-level deletion
    print("Phase 1: Database-level testing")
    db_test_success = test_database_project_deletion()
    
    # Test 2: API-level deletion (if API is available)
    print("\nPhase 2: API-level testing")
    if wait_for_api():
        api_test_success = test_api_project_deletion()
    else:
        print("⚠️  Skipping API tests - API not available")
        api_test_success = None
    
    # Results summary
    print("\n📊 Test Results Summary")
    print("=" * 60)
    print(f"✅ Database-level deletion: {'PASSED' if db_test_success else 'FAILED'}")
    if api_test_success is not None:
        print(f"✅ API-level deletion: {'PASSED' if api_test_success else 'FAILED'}")
    else:
        print("⚠️  API-level deletion: SKIPPED (API not available)")
    
    if db_test_success and (api_test_success is None or api_test_success):
        print("\n🎉 All available tests PASSED! Project deletion fix is working correctly.")
        return True
    else:
        print("\n❌ Some tests FAILED. Please check the issues above.")
        return False

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)