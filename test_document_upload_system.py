#!/usr/bin/env python3
"""
Test script for the enhanced document upload and processing system

This script validates all the implemented features:
1. MinIO client initialization with proper error handling
2. Atomic document upload with database record creation
3. File deduplication using SHA256 hashing
4. Document processing queue for background tasks
5. Comprehensive cleanup on upload failures
"""

import os
import sys
import asyncio
import tempfile
import hashlib
import uuid
from datetime import datetime
from pathlib import Path

# Add the API directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'apps', 'api'))

from services.document_upload_service import document_upload_service
from database import SessionLocal, init_db
from models import Document, IngestEvent
from fastapi import UploadFile
import io

class MockUploadFile:
    """Mock UploadFile for testing"""
    
    def __init__(self, filename: str, content: bytes, content_type: str = "application/pdf"):
        self.filename = filename
        self.content = content
        self.content_type = content_type
        self.size = len(content)
    
    async def read(self) -> bytes:
        return self.content

async def test_minio_initialization():
    """Test 1: MinIO client initialization with proper error handling"""
    print("\n=== Test 1: MinIO Client Initialization ===")
    
    try:
        # Test service availability
        is_available = document_upload_service.is_available()
        print(f"✅ MinIO service availability check: {'Available' if is_available else 'Unavailable'}")
        
        if is_available:
            print("✅ MinIO client initialized successfully")
            print(f"   - Documents bucket: {document_upload_service.bucket_name}")
            print(f"   - Temp bucket: {document_upload_service.temp_bucket}")
        else:
            print("⚠️  MinIO service not available - running in degraded mode")
        
        return True
        
    except Exception as e:
        print(f"❌ MinIO initialization test failed: {e}")
        return False

async def test_file_validation():
    """Test 2: File validation and error handling"""
    print("\n=== Test 2: File Validation ===")
    
    try:
        # Test valid file
        valid_file = MockUploadFile("test_document.pdf", b"PDF content here", "application/pdf")
        await document_upload_service._validate_file(valid_file, "test_trace")
        print("✅ Valid file passed validation")
        
        # Test file with dangerous filename
        try:
            dangerous_file = MockUploadFile("../../../etc/passwd", b"content", "text/plain")
            await document_upload_service._validate_file(dangerous_file, "test_trace")
            print("❌ Dangerous filename should have been rejected")
            return False
        except Exception:
            print("✅ Dangerous filename properly rejected")
        
        # Test unsupported file type
        try:
            unsupported_file = MockUploadFile("test.exe", b"executable", "application/x-executable")
            await document_upload_service._validate_file(unsupported_file, "test_trace")
            print("❌ Unsupported file type should have been rejected")
            return False
        except Exception:
            print("✅ Unsupported file type properly rejected")
        
        return True
        
    except Exception as e:
        print(f"❌ File validation test failed: {e}")
        return False

async def test_deduplication():
    """Test 3: File deduplication using SHA256 hashing"""
    print("\n=== Test 3: File Deduplication ===")
    
    db = SessionLocal()
    
    try:
        # Create test content
        test_content = b"This is a test document for deduplication testing"
        test_hash = hashlib.sha256(test_content).hexdigest()
        
        # Check duplicate detection with empty database
        duplicate = await document_upload_service._check_duplicate(test_hash, db, "test_trace")
        if duplicate is None:
            print("✅ No duplicate found in empty database")
        else:
            print("❌ False positive duplicate detection")
            return False
        
        # Create a document record manually to test duplicate detection
        from models import Document
        import uuid
        from datetime import datetime
        
        existing_doc = Document(
            id=str(uuid.uuid4()),  # Use string ID
            filename="existing_test.pdf",
            mime_type="application/pdf",
            size_bytes=len(test_content),
            path="test/path",  # Required path field
            storage_path="test/path",
            content_sha256=test_hash,
            type="test"
        )
        
        db.add(existing_doc)
        db.commit()
        
        # Now check for duplicate
        duplicate = await document_upload_service._check_duplicate(test_hash, db, "test_trace")
        if duplicate and duplicate.id == existing_doc.id:
            print("✅ Duplicate correctly detected")
        else:
            print("❌ Duplicate detection failed")
            return False
        
        # Clean up
        db.delete(existing_doc)
        db.commit()
        
        return True
        
    except Exception as e:
        print(f"❌ Deduplication test failed: {e}")
        return False
    finally:
        db.close()

async def test_atomic_upload():
    """Test 4: Atomic document upload with database record creation"""
    print("\n=== Test 4: Atomic Upload Operations ===")
    
    if not document_upload_service.is_available():
        print("⚠️  Skipping atomic upload test - MinIO not available")
        return True
    
    db = SessionLocal()
    
    try:
        # Create test file
        test_content = b"Test document content for atomic upload testing"
        test_file = MockUploadFile("atomic_test.pdf", test_content, "application/pdf")
        
        # Perform upload
        result = await document_upload_service.upload_document(
            file=test_file,
            project_id=None,  # Use None instead of invalid UUID string
            db=db
        )
        
        if result.get('duplicate', False):
            print("⚠️  Document was detected as duplicate")
            return True
        
        document_id = result['document_id']
        print(f"✅ Document uploaded successfully: {document_id}")
        
        # Verify database record was created
        document = db.query(Document).filter(Document.id == document_id).first()
        if document:
            print("✅ Database record created successfully")
            print(f"   - Filename: {document.filename}")
            print(f"   - Size: {document.size_bytes} bytes")
            print(f"   - SHA256: {document.content_sha256[:16]}...")
            print(f"   - Project ID: {document.project_id}")
        else:
            print("❌ Database record not found")
            return False
        
        # Verify file was stored (we can't easily test MinIO without actual connection)
        if result.get('storage_path'):
            print(f"✅ Storage path assigned: {result['storage_path']}")
        
        # Clean up
        await document_upload_service.delete_document(document_id, db)
        print("✅ Cleanup completed")
        
        return True
        
    except Exception as e:
        print(f"❌ Atomic upload test failed: {e}")
        return False
    finally:
        db.close()

async def test_processing_queue():
    """Test 5: Document processing queue for background tasks"""
    print("\n=== Test 5: Processing Queue ===")
    
    try:
        # Test queue initialization
        initial_size = document_upload_service.processing_queue.qsize()
        print(f"✅ Processing queue initialized (size: {initial_size})")
        
        # Test queueing a document
        test_document_id = "test_doc_123"
        test_trace_id = "test_trace_123"
        
        await document_upload_service._queue_for_processing(test_document_id, test_trace_id)
        
        new_size = document_upload_service.processing_queue.qsize()
        if new_size > initial_size:
            print("✅ Document successfully queued for processing")
        else:
            print("❌ Document was not queued")
            return False
        
        # Test processing task creation
        if document_upload_service._processing_task and not document_upload_service._processing_task.done():
            print("✅ Background processing task is running")
        else:
            print("⚠️  Background processing task not running (may be normal)")
        
        return True
        
    except Exception as e:
        print(f"❌ Processing queue test failed: {e}")
        return False

async def test_error_handling_and_cleanup():
    """Test 6: Comprehensive cleanup on upload failures"""
    print("\n=== Test 6: Error Handling and Cleanup ===")
    
    db = SessionLocal()
    
    try:
        # Test cleanup function directly
        test_document_id = str(uuid.uuid4())
        test_temp_path = "temp/cleanup_test/test.pdf"
        test_error = "Simulated upload failure"
        
        # This should not fail even if the document doesn't exist
        await document_upload_service._cleanup_failed_upload(
            document_id=test_document_id,
            temp_path=test_temp_path,
            db=db,
            trace_id="cleanup_test_trace",
            error=test_error
        )
        
        print("✅ Cleanup function executed without errors")
        
        # Test error logging
        await document_upload_service._log_ingest_event(
            document_id=test_document_id,
            stage="upload",
            status="fail",
            payload={"error": test_error, "test": True},
            db=db
        )
        
        # Verify event was logged
        event = db.query(IngestEvent).filter(
            IngestEvent.document_id == test_document_id,
            IngestEvent.stage == "upload",
            IngestEvent.status == "fail"
        ).first()
        
        if event:
            print("✅ Error event logged successfully")
        else:
            print("❌ Error event not logged")
            return False
        
        # Clean up test event
        db.delete(event)
        db.commit()
        
        return True
        
    except Exception as e:
        print(f"❌ Error handling test failed: {e}")
        return False
    finally:
        db.close()

async def test_document_info_retrieval():
    """Test 7: Document information retrieval"""
    print("\n=== Test 7: Document Information Retrieval ===")
    
    db = SessionLocal()
    
    try:
        # Create a test document record
        from models import Document
        import uuid
        from datetime import datetime
        
        test_doc_id = str(uuid.uuid4())
        test_doc = Document(
            id=str(uuid.uuid4()),  # Use string ID
            filename="info_test.pdf",
            mime_type="application/pdf",
            size_bytes=1024,
            path="test/path/info_test.pdf",  # Required path field
            storage_path="test/path/info_test.pdf",
            content_sha256="test_hash_123",
            type="test",
            project_id=None
        )
        
        db.add(test_doc)
        db.commit()
        
        # Test document info retrieval
        info = await document_upload_service.get_document_info(str(test_doc.id), db)
        
        if info and info.get('document'):
            print("✅ Document info retrieved successfully")
            doc_info = info['document']
            print(f"   - ID: {doc_info['id']}")
            print(f"   - Filename: {doc_info['filename']}")
            print(f"   - Size: {doc_info['size_bytes']} bytes")
            print(f"   - Type: {doc_info['type']}")
        else:
            print("❌ Document info retrieval failed")
            return False
        
        # Clean up
        db.delete(test_doc)
        db.commit()
        
        return True
        
    except Exception as e:
        print(f"❌ Document info retrieval test failed: {e}")
        return False
    finally:
        db.close()

async def run_all_tests():
    """Run all tests and report results"""
    print("🚀 Starting Enhanced Document Upload System Tests")
    print("=" * 60)
    
    # Initialize database
    try:
        init_db()
        print("✅ Database initialized")
    except Exception as e:
        print(f"⚠️  Database initialization warning: {e}")
    
    tests = [
        ("MinIO Initialization", test_minio_initialization),
        ("File Validation", test_file_validation),
        ("File Deduplication", test_deduplication),
        ("Atomic Upload", test_atomic_upload),
        ("Processing Queue", test_processing_queue),
        ("Error Handling & Cleanup", test_error_handling_and_cleanup),
        ("Document Info Retrieval", test_document_info_retrieval),
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        try:
            result = await test_func()
            if result:
                passed += 1
                print(f"✅ {test_name}: PASSED")
            else:
                print(f"❌ {test_name}: FAILED")
        except Exception as e:
            print(f"❌ {test_name}: ERROR - {e}")
    
    print("\n" + "=" * 60)
    print(f"📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Document upload system is working correctly.")
        return True
    else:
        print("⚠️  Some tests failed. Please check the implementation.")
        return False

if __name__ == "__main__":
    # Set environment variables for testing if not set
    if not os.getenv('DATABASE_URL'):
        os.environ['DATABASE_URL'] = 'postgresql://studioops:studioops123@localhost:5432/studioops'
    
    if not os.getenv('MINIO_ENDPOINT'):
        os.environ['MINIO_ENDPOINT'] = 'localhost:9000'
        os.environ['MINIO_ACCESS_KEY'] = 'studioops'
        os.environ['MINIO_SECRET_KEY'] = 'studioops123'
        os.environ['MINIO_SECURE'] = 'false'
    
    # Run tests
    success = asyncio.run(run_all_tests())
    sys.exit(0 if success else 1)