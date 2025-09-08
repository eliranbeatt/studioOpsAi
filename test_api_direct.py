#!/usr/bin/env python3
"""
Direct API test for project deletion
"""

import sys
import os
sys.path.insert(0, 'apps/api')

from fastapi.testclient import TestClient
import uuid

# Import the app from the API directory
try:
    from main import app
except ImportError as e:
    print(f"Failed to import app: {e}")
    sys.exit(1)

def test_project_deletion_direct():
    """Test project deletion using FastAPI TestClient"""
    
    print("🧪 Testing Project Deletion via TestClient")
    print("=" * 50)
    
    client = TestClient(app)
    
    try:
        # 1. Create a test project
        print("1. Creating test project...")
        project_data = {
            "name": f"Direct Test Project {uuid.uuid4().hex[:8]}",
            "client_name": "Direct Test Client",
            "status": "active"
        }
        
        response = client.post("/projects", json=project_data)
        if response.status_code != 200:
            print(f"❌ Failed to create project: {response.status_code}")
            print(f"   Response: {response.text}")
            return False
        
        project = response.json()
        project_id = project["id"]
        print(f"✅ Created project: {project['name']} (ID: {project_id})")
        
        # 2. Get deletion impact analysis
        print("2. Getting deletion impact analysis...")
        response = client.get(f"/projects/{project_id}/deletion-impact")
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
            print(f"   Response: {response.text}")
        
        # 3. Delete the project
        print("3. Deleting project...")
        response = client.delete(f"/projects/{project_id}")
        
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
            response = client.get(f"/projects/{project_id}")
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
        print(f"❌ Direct API test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_project_deletion_direct()
    print(f"\n{'✅ SUCCESS' if success else '❌ FAILED'}")
    exit(0 if success else 1)