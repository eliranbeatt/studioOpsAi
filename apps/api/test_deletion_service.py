#!/usr/bin/env python3
"""
Test the project deletion service directly
"""

import asyncio
import uuid
from sqlalchemy.orm import Session
from database import get_db
from services.project_deletion_service import project_deletion_service
from models import Project

async def test_deletion_service():
    """Test the project deletion service directly"""
    
    print("🧪 Testing Project Deletion Service")
    print("=" * 40)
    
    # Get database session
    db = next(get_db())
    
    try:
        # 1. Create a test project
        print("1. Creating test project...")
        test_project = Project(
            name=f"Service Test Project {uuid.uuid4().hex[:8]}",
            client_name="Service Test Client",
            status="active"
        )
        
        db.add(test_project)
        db.commit()
        db.refresh(test_project)
        
        project_id = test_project.id
        print(f"✅ Created project: {test_project.name} (ID: {project_id})")
        
        # 2. Test validation
        print("2. Testing deletion validation...")
        validation = await project_deletion_service.validate_project_deletion(project_id, db)
        print(f"✅ Validation result:")
        print(f"   - Can delete: {validation.get('can_delete', False)}")
        print(f"   - Project name: {validation.get('project_name', 'Unknown')}")
        print(f"   - Safe deletion: {validation.get('safe_deletion', False)}")
        
        if validation.get('warnings'):
            for warning in validation['warnings']:
                print(f"   - Warning: {warning}")
        
        # 3. Test deletion
        print("3. Testing project deletion...")
        result = await project_deletion_service.delete_project_safely(project_id, db)
        
        print(f"✅ Deletion result:")
        print(f"   - Success: {result.get('success', False)}")
        print(f"   - Message: {result.get('message', 'No message')}")
        print(f"   - Project name: {result.get('project_name', 'Unknown')}")
        
        if 'deletion_stats' in result:
            stats = result['deletion_stats']
            print(f"   - Chat sessions unlinked: {stats.get('chat_sessions_unlinked', 0)}")
            print(f"   - Documents unlinked: {stats.get('documents_unlinked', 0)}")
            print(f"   - Purchases unlinked: {stats.get('purchases_unlinked', 0)}")
            print(f"   - Plans deleted: {stats.get('plans_deleted', 0)}")
        
        # 4. Verify deletion
        print("4. Verifying project deletion...")
        deleted_project = db.query(Project).filter(Project.id == project_id).first()
        if deleted_project is None:
            print("✅ Project successfully deleted from database")
            return True
        else:
            print("❌ Project still exists in database")
            return False
    
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    finally:
        db.close()

if __name__ == "__main__":
    success = asyncio.run(test_deletion_service())
    print(f"\n{'✅ SUCCESS' if success else '❌ FAILED'}")
    exit(0 if success else 1)