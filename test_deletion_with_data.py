#!/usr/bin/env python3
"""
Test project deletion with related data
"""

import requests
import psycopg2
import uuid
import os
import time
from dotenv import load_dotenv

load_dotenv()

API_BASE_URL = "http://localhost:8000"

def test_deletion_with_related_data():
    """Test project deletion when there are related records"""
    
    print("🧪 Testing Project Deletion with Related Data")
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
        # 1. Create a test project via API
        print("1. Creating test project via API...")
        project_data = {
            "name": f"Data Test Project {uuid.uuid4().hex[:8]}",
            "client_name": "Data Test Client",
            "status": "active"
        }
        
        response = requests.post(f"{API_BASE_URL}/projects", json=project_data, timeout=10)
        if response.status_code != 200:
            print(f"❌ Failed to create project: {response.status_code}")
            return False
        
        project = response.json()
        project_id = project["id"]
        print(f"✅ Created project: {project['name']} (ID: {project_id})")
        
        # 2. Add related data directly to database
        print("2. Adding related data to database...")
        conn = psycopg2.connect(**db_params)
        cursor = conn.cursor()
        
        # Add a chat session
        chat_session_id = str(uuid.uuid4())
        cursor.execute("""
            INSERT INTO chat_sessions (id, project_id, title, user_id)
            VALUES (%s, %s, %s, %s)
        """, (chat_session_id, project_id, "Test Chat Session", "test_user"))
        
        # Add a document
        document_id = str(uuid.uuid4())
        cursor.execute("""
            INSERT INTO documents (id, project_id, type, path)
            VALUES (%s, %s, %s, %s)
        """, (document_id, project_id, "test", "/test/path"))
        
        # Add a purchase
        purchase_id = str(uuid.uuid4())
        cursor.execute("""
            INSERT INTO purchases (id, project_id, qty, unit_price_nis)
            VALUES (%s, %s, %s, %s)
        """, (purchase_id, project_id, 10, 150.75))
        
        # Add a plan
        plan_id = str(uuid.uuid4())
        cursor.execute("""
            INSERT INTO plans (id, project_id, version, status)
            VALUES (%s, %s, %s, %s)
        """, (plan_id, project_id, 1, "draft"))
        
        # Add a plan item
        plan_item_id = str(uuid.uuid4())
        cursor.execute("""
            INSERT INTO plan_items (id, plan_id, category, title, quantity)
            VALUES (%s, %s, %s, %s, %s)
        """, (plan_item_id, plan_id, "materials", "Test Material", 5))
        
        conn.commit()
        print("✅ Added related data: 1 chat session, 1 document, 1 purchase, 1 plan, 1 plan item")
        
        # 3. Get deletion impact analysis
        print("3. Getting deletion impact analysis...")
        response = requests.get(f"{API_BASE_URL}/projects/{project_id}/deletion-impact", timeout=10)
        if response.status_code == 200:
            impact = response.json()
            print(f"✅ Deletion impact analysis:")
            print(f"   - Can delete: {impact.get('can_delete', False)}")
            print(f"   - Project name: {impact.get('project_name', 'Unknown')}")
            print(f"   - Safe deletion: {impact.get('safe_deletion', False)}")
            
            if 'impact_summary' in impact:
                summary = impact['impact_summary']
                print(f"   - Chat sessions: {summary.get('chat_sessions', 0)}")
                print(f"   - Documents: {summary.get('documents', 0)}")
                print(f"   - Purchases: {summary.get('purchases', 0)}")
                print(f"   - Plans: {summary.get('plans', 0)}")
                print(f"   - Plan items: {summary.get('plan_items', 0)}")
            
            if impact.get('warnings'):
                for warning in impact['warnings']:
                    print(f"   - Warning: {warning}")
        else:
            print(f"⚠️  Could not get deletion impact: {response.status_code}")
        
        # 4. Delete the project via API
        print("4. Deleting project via API...")
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
                print(f"   - Plan items deleted: {stats.get('plan_items_deleted', 0)}")
        else:
            print(f"❌ Project deletion failed: {response.status_code}")
            print(f"   Response: {response.text}")
            return False
        
        # 5. Verify the related data handling
        print("5. Verifying related data handling...")
        
        # Check chat session (should be unlinked)
        cursor.execute("SELECT project_id FROM chat_sessions WHERE id = %s", (chat_session_id,))
        chat_result = cursor.fetchone()
        if chat_result and chat_result[0] is None:
            print("   ✅ Chat session project_id set to NULL")
        else:
            print(f"   ❌ Chat session not handled correctly: {chat_result}")
            return False
        
        # Check document (should be unlinked)
        cursor.execute("SELECT project_id FROM documents WHERE id = %s", (document_id,))
        doc_result = cursor.fetchone()
        if doc_result and doc_result[0] is None:
            print("   ✅ Document project_id set to NULL")
        else:
            print(f"   ❌ Document not handled correctly: {doc_result}")
            return False
        
        # Check purchase (should be unlinked)
        cursor.execute("SELECT project_id FROM purchases WHERE id = %s", (purchase_id,))
        purchase_result = cursor.fetchone()
        if purchase_result and purchase_result[0] is None:
            print("   ✅ Purchase project_id set to NULL")
        else:
            print(f"   ❌ Purchase not handled correctly: {purchase_result}")
            return False
        
        # Check plan (should be deleted)
        cursor.execute("SELECT id FROM plans WHERE id = %s", (plan_id,))
        plan_result = cursor.fetchone()
        if plan_result is None:
            print("   ✅ Plan deleted")
        else:
            print(f"   ❌ Plan not deleted: {plan_result}")
            return False
        
        # Check plan item (should be deleted via cascade)
        cursor.execute("SELECT id FROM plan_items WHERE id = %s", (plan_item_id,))
        plan_item_result = cursor.fetchone()
        if plan_item_result is None:
            print("   ✅ Plan item deleted via cascade")
        else:
            print(f"   ❌ Plan item not deleted: {plan_item_result}")
            return False
        
        # 6. Verify project is deleted
        print("6. Verifying project deletion...")
        response = requests.get(f"{API_BASE_URL}/projects/{project_id}", timeout=10)
        if response.status_code == 404:
            print("✅ Project successfully deleted - returns 404 as expected")
            return True
        else:
            print(f"❌ Project still exists after deletion: {response.status_code}")
            return False
    
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    finally:
        try:
            cursor.close()
            conn.close()
        except:
            pass

if __name__ == "__main__":
    success = test_deletion_with_related_data()
    print(f"\n{'✅ SUCCESS' if success else '❌ FAILED'}")
    exit(0 if success else 1)