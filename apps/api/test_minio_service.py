"""Test MinIO service functionality"""

import os
import tempfile
import pytest
from pathlib import Path

from services.minio_service import minio_service

def test_minio_service_initialization():
    """Test that MinIO service initializes properly"""
    # Should not raise an exception even if MinIO is not available
    assert minio_service is not None
    
    # Check if service reports availability correctly
    is_available = minio_service.is_available()
    assert isinstance(is_available, bool)

def test_bucket_configuration():
    """Test that bucket configuration is loaded correctly"""
    expected_buckets = ['documents', 'uploads', 'exports', 'temp']
    
    for bucket_type in expected_buckets:
        assert bucket_type in minio_service.buckets
        assert minio_service.buckets[bucket_type] == bucket_type

@pytest.mark.skipif(not minio_service.is_available(), reason="MinIO service not available")
def test_file_upload_and_download():
    """Test file upload and download functionality"""
    # Create a temporary test file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as temp_file:
        temp_file.write("Test content for MinIO upload")
        temp_file_path = temp_file.name
    
    try:
        # Test upload
        object_path = minio_service.upload_file(
            file_path=temp_file_path,
            bucket_name='temp',
            object_name='test_upload.txt',
            metadata={'test': 'true'}
        )
        
        assert object_path is not None
        assert object_path == 'temp/test_upload.txt'
        
        # Test download
        download_path = minio_service.download_file('temp', 'test_upload.txt')
        assert download_path is not None
        assert os.path.exists(download_path)
        
        # Verify content
        with open(download_path, 'r') as f:
            content = f.read()
            assert content == "Test content for MinIO upload"
        
        # Clean up downloaded file
        os.unlink(download_path)
        
        # Test deletion
        deleted = minio_service.delete_object('temp', 'test_upload.txt')
        assert deleted is True
        
    finally:
        # Clean up test file
        if os.path.exists(temp_file_path):
            os.unlink(temp_file_path)

@pytest.mark.skipif(not minio_service.is_available(), reason="MinIO service not available")
def test_data_upload():
    """Test uploading binary data directly"""
    test_data = b"Binary test data for MinIO"
    
    # Test upload
    object_path = minio_service.upload_data(
        data=test_data,
        bucket_name='temp',
        object_name='test_binary.bin',
        content_type='application/octet-stream',
        metadata={'type': 'binary_test'}
    )
    
    assert object_path is not None
    assert object_path == 'temp/test_binary.bin'
    
    # Test retrieval
    retrieved_data = minio_service.get_object_data('temp', 'test_binary.bin')
    assert retrieved_data == test_data
    
    # Clean up
    deleted = minio_service.delete_object('temp', 'test_binary.bin')
    assert deleted is True

@pytest.mark.skipif(not minio_service.is_available(), reason="MinIO service not available")
def test_document_storage():
    """Test document storage with organized paths"""
    # Create a temporary test document
    with tempfile.NamedTemporaryFile(mode='w', suffix='.pdf', delete=False) as temp_file:
        temp_file.write("Mock PDF content")
        temp_file_path = temp_file.name
    
    try:
        # Test document storage
        object_path = minio_service.store_document(
            file_path=temp_file_path,
            project_id='test-project-123',
            document_type='quote',
            metadata={'client': 'test_client'}
        )
        
        assert object_path is not None
        assert 'documents/projects/test-project-123/quote/' in object_path
        
        # Extract object name from path
        object_name = object_path.split('/', 1)[1]  # Remove bucket name
        
        # Test retrieval
        download_path = minio_service.download_file('documents', object_name)
        assert download_path is not None
        assert os.path.exists(download_path)
        
        # Clean up
        os.unlink(download_path)
        deleted = minio_service.delete_object('documents', object_name)
        assert deleted is True
        
    finally:
        # Clean up test file
        if os.path.exists(temp_file_path):
            os.unlink(temp_file_path)

@pytest.mark.skipif(not minio_service.is_available(), reason="MinIO service not available")
def test_temp_file_cleanup():
    """Test temporary file cleanup functionality"""
    process_id = 'test-process-456'
    
    # Create multiple temp files
    temp_files = []
    for i in range(3):
        with tempfile.NamedTemporaryFile(mode='w', suffix=f'_{i}.txt', delete=False) as temp_file:
            temp_file.write(f"Temp file {i}")
            temp_file_path = temp_file.name
            temp_files.append(temp_file_path)
            
            # Store as temp file
            object_path = minio_service.store_temp_file(
                file_path=temp_file_path,
                process_id=process_id,
                metadata={'index': str(i)}
            )
            assert object_path is not None
    
    try:
        # Test cleanup
        deleted_count = minio_service.cleanup_temp_files(process_id)
        assert deleted_count == 3
        
        # Verify files are gone
        objects = minio_service.list_objects('temp', prefix=f'temp/{process_id}/')
        assert len(objects) == 0
        
    finally:
        # Clean up local temp files
        for temp_file_path in temp_files:
            if os.path.exists(temp_file_path):
                os.unlink(temp_file_path)

def test_graceful_degradation():
    """Test that service degrades gracefully when MinIO is unavailable"""
    # This test should pass even when MinIO is not available
    
    # These operations should return None/False/empty when service is unavailable
    if not minio_service.is_available():
        result = minio_service.upload_file('/nonexistent/file.txt', 'test', 'test.txt')
        assert result is None
        
        result = minio_service.download_file('test', 'test.txt')
        assert result is None
        
        result = minio_service.get_object_data('test', 'test.txt')
        assert result is None
        
        result = minio_service.delete_object('test', 'test.txt')
        assert result is False
        
        result = minio_service.list_objects('test')
        assert result == []

if __name__ == "__main__":
    # Run basic tests
    test_minio_service_initialization()
    test_bucket_configuration()
    test_graceful_degradation()
    
    if minio_service.is_available():
        print("MinIO service is available - running full tests")
        test_file_upload_and_download()
        test_data_upload()
        test_document_storage()
        test_temp_file_cleanup()
        print("All MinIO tests passed!")
    else:
        print("MinIO service not available - skipped integration tests")
        print("Basic functionality tests passed!")