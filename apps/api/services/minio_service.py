"""MinIO service for document storage and retrieval"""

import os
import logging
from typing import Optional, Dict, Any, List, BinaryIO
from datetime import datetime, timedelta
from pathlib import Path
import tempfile
import uuid

try:
    from minio import Minio
    from minio.error import S3Error
    MINIO_AVAILABLE = True
except ImportError:
    MINIO_AVAILABLE = False
    logging.warning("MinIO client not available. Install with: pip install minio")

logger = logging.getLogger(__name__)

class MinIOService:
    """Service for interacting with MinIO object storage"""
    
    def __init__(self):
        self.client = None
        self.buckets = {
            'documents': os.getenv('MINIO_DOCUMENTS_BUCKET', 'documents'),
            'uploads': os.getenv('MINIO_UPLOADS_BUCKET', 'uploads'),
            'exports': os.getenv('MINIO_EXPORTS_BUCKET', 'exports'),
            'temp': os.getenv('MINIO_TEMP_BUCKET', 'temp')
        }
        
        if MINIO_AVAILABLE:
            self._initialize_client()
        else:
            logger.warning("MinIO service initialized without client (minio package not available)")
    
    def _initialize_client(self):
        """Initialize MinIO client with configuration"""
        try:
            endpoint = os.getenv('MINIO_ENDPOINT', 'localhost:9000')
            access_key = os.getenv('MINIO_ACCESS_KEY', 'studioops')
            secret_key = os.getenv('MINIO_SECRET_KEY', 'studioops123')
            secure = os.getenv('MINIO_SECURE', 'false').lower() == 'true'
            region = os.getenv('MINIO_REGION', 'us-east-1')
            
            self.client = Minio(
                endpoint=endpoint,
                access_key=access_key,
                secret_key=secret_key,
                secure=secure,
                region=region
            )
            
            # Test connection
            self.client.list_buckets()
            logger.info(f"MinIO client initialized successfully for endpoint: {endpoint}")
            
        except Exception as e:
            logger.error(f"Failed to initialize MinIO client: {e}")
            self.client = None
    
    def is_available(self) -> bool:
        """Check if MinIO service is available"""
        return MINIO_AVAILABLE and self.client is not None
    
    def upload_file(self, 
                   file_path: str, 
                   bucket_name: str, 
                   object_name: Optional[str] = None,
                   content_type: Optional[str] = None,
                   metadata: Optional[Dict[str, str]] = None) -> Optional[str]:
        """Upload a file to MinIO bucket"""
        
        if not self.is_available():
            logger.warning("MinIO service not available for file upload")
            return None
        
        try:
            if object_name is None:
                object_name = Path(file_path).name
            
            # Ensure bucket exists
            if not self.client.bucket_exists(bucket_name):
                logger.warning(f"Bucket {bucket_name} does not exist")
                return None
            
            # Upload file
            result = self.client.fput_object(
                bucket_name=bucket_name,
                object_name=object_name,
                file_path=file_path,
                content_type=content_type,
                metadata=metadata
            )
            
            logger.info(f"File uploaded successfully: {bucket_name}/{object_name}")
            return f"{bucket_name}/{object_name}"
            
        except S3Error as e:
            logger.error(f"MinIO S3 error during upload: {e}")
            return None
        except Exception as e:
            logger.error(f"Error uploading file to MinIO: {e}")
            return None
    
    def upload_data(self, 
                   data: bytes, 
                   bucket_name: str, 
                   object_name: str,
                   content_type: Optional[str] = None,
                   metadata: Optional[Dict[str, str]] = None) -> Optional[str]:
        """Upload binary data to MinIO bucket"""
        
        if not self.is_available():
            logger.warning("MinIO service not available for data upload")
            return None
        
        try:
            from io import BytesIO
            
            # Ensure bucket exists
            if not self.client.bucket_exists(bucket_name):
                logger.warning(f"Bucket {bucket_name} does not exist")
                return None
            
            # Upload data
            result = self.client.put_object(
                bucket_name=bucket_name,
                object_name=object_name,
                data=BytesIO(data),
                length=len(data),
                content_type=content_type,
                metadata=metadata
            )
            
            logger.info(f"Data uploaded successfully: {bucket_name}/{object_name}")
            return f"{bucket_name}/{object_name}"
            
        except S3Error as e:
            logger.error(f"MinIO S3 error during data upload: {e}")
            return None
        except Exception as e:
            logger.error(f"Error uploading data to MinIO: {e}")
            return None
    
    def download_file(self, 
                     bucket_name: str, 
                     object_name: str, 
                     file_path: Optional[str] = None) -> Optional[str]:
        """Download a file from MinIO bucket"""
        
        if not self.is_available():
            logger.warning("MinIO service not available for file download")
            return None
        
        try:
            if file_path is None:
                # Create temporary file
                temp_dir = tempfile.gettempdir()
                file_path = os.path.join(temp_dir, f"minio_download_{uuid.uuid4().hex}_{object_name}")
            
            # Download file
            self.client.fget_object(
                bucket_name=bucket_name,
                object_name=object_name,
                file_path=file_path
            )
            
            logger.info(f"File downloaded successfully: {bucket_name}/{object_name} -> {file_path}")
            return file_path
            
        except S3Error as e:
            logger.error(f"MinIO S3 error during download: {e}")
            return None
        except Exception as e:
            logger.error(f"Error downloading file from MinIO: {e}")
            return None
    
    def get_object_data(self, bucket_name: str, object_name: str) -> Optional[bytes]:
        """Get object data as bytes"""
        
        if not self.is_available():
            logger.warning("MinIO service not available for object retrieval")
            return None
        
        try:
            response = self.client.get_object(bucket_name, object_name)
            data = response.read()
            response.close()
            response.release_conn()
            
            logger.info(f"Object data retrieved successfully: {bucket_name}/{object_name}")
            return data
            
        except S3Error as e:
            logger.error(f"MinIO S3 error during object retrieval: {e}")
            return None
        except Exception as e:
            logger.error(f"Error retrieving object data from MinIO: {e}")
            return None
    
    def delete_object(self, bucket_name: str, object_name: str) -> bool:
        """Delete an object from MinIO bucket"""
        
        if not self.is_available():
            logger.warning("MinIO service not available for object deletion")
            return False
        
        try:
            self.client.remove_object(bucket_name, object_name)
            logger.info(f"Object deleted successfully: {bucket_name}/{object_name}")
            return True
            
        except S3Error as e:
            logger.error(f"MinIO S3 error during deletion: {e}")
            return False
        except Exception as e:
            logger.error(f"Error deleting object from MinIO: {e}")
            return False
    
    def list_objects(self, 
                    bucket_name: str, 
                    prefix: Optional[str] = None,
                    recursive: bool = True) -> List[Dict[str, Any]]:
        """List objects in a MinIO bucket"""
        
        if not self.is_available():
            logger.warning("MinIO service not available for object listing")
            return []
        
        try:
            objects = []
            for obj in self.client.list_objects(bucket_name, prefix=prefix, recursive=recursive):
                objects.append({
                    'name': obj.object_name,
                    'size': obj.size,
                    'last_modified': obj.last_modified,
                    'etag': obj.etag,
                    'content_type': obj.content_type
                })
            
            logger.info(f"Listed {len(objects)} objects from {bucket_name}")
            return objects
            
        except S3Error as e:
            logger.error(f"MinIO S3 error during listing: {e}")
            return []
        except Exception as e:
            logger.error(f"Error listing objects from MinIO: {e}")
            return []
    
    def get_presigned_url(self, 
                         bucket_name: str, 
                         object_name: str,
                         expires: timedelta = timedelta(hours=1),
                         method: str = "GET") -> Optional[str]:
        """Generate a presigned URL for object access"""
        
        if not self.is_available():
            logger.warning("MinIO service not available for presigned URL generation")
            return None
        
        try:
            if method.upper() == "GET":
                url = self.client.presigned_get_object(bucket_name, object_name, expires=expires)
            elif method.upper() == "PUT":
                url = self.client.presigned_put_object(bucket_name, object_name, expires=expires)
            else:
                logger.error(f"Unsupported method for presigned URL: {method}")
                return None
            
            logger.info(f"Generated presigned URL for {bucket_name}/{object_name}")
            return url
            
        except S3Error as e:
            logger.error(f"MinIO S3 error during presigned URL generation: {e}")
            return None
        except Exception as e:
            logger.error(f"Error generating presigned URL: {e}")
            return None
    
    def store_document(self, 
                      file_path: str, 
                      project_id: str,
                      document_type: str = "document",
                      metadata: Optional[Dict[str, str]] = None) -> Optional[str]:
        """Store a document with organized path structure"""
        
        if not metadata:
            metadata = {}
        
        # Add standard metadata
        metadata.update({
            'project_id': project_id,
            'document_type': document_type,
            'uploaded_at': datetime.utcnow().isoformat()
        })
        
        # Create organized object name
        file_name = Path(file_path).name
        object_name = f"projects/{project_id}/{document_type}/{file_name}"
        
        return self.upload_file(
            file_path=file_path,
            bucket_name=self.buckets['documents'],
            object_name=object_name,
            metadata=metadata
        )
    
    def store_export(self, 
                    file_path: str, 
                    project_id: str,
                    export_type: str = "pdf",
                    metadata: Optional[Dict[str, str]] = None) -> Optional[str]:
        """Store an exported document (PDF, etc.)"""
        
        if not metadata:
            metadata = {}
        
        # Add standard metadata
        metadata.update({
            'project_id': project_id,
            'export_type': export_type,
            'generated_at': datetime.utcnow().isoformat()
        })
        
        # Create organized object name
        file_name = Path(file_path).name
        object_name = f"exports/{project_id}/{export_type}/{file_name}"
        
        return self.upload_file(
            file_path=file_path,
            bucket_name=self.buckets['exports'],
            object_name=object_name,
            metadata=metadata
        )
    
    def store_temp_file(self, 
                       file_path: str, 
                       process_id: str,
                       metadata: Optional[Dict[str, str]] = None) -> Optional[str]:
        """Store a temporary processing file"""
        
        if not metadata:
            metadata = {}
        
        # Add standard metadata
        metadata.update({
            'process_id': process_id,
            'temp_file': 'true',
            'created_at': datetime.utcnow().isoformat()
        })
        
        # Create organized object name
        file_name = Path(file_path).name
        object_name = f"temp/{process_id}/{file_name}"
        
        return self.upload_file(
            file_path=file_path,
            bucket_name=self.buckets['temp'],
            object_name=object_name,
            metadata=metadata
        )
    
    def cleanup_temp_files(self, process_id: str) -> int:
        """Clean up temporary files for a process"""
        
        if not self.is_available():
            return 0
        
        try:
            prefix = f"temp/{process_id}/"
            objects = self.list_objects(self.buckets['temp'], prefix=prefix)
            
            deleted_count = 0
            for obj in objects:
                if self.delete_object(self.buckets['temp'], obj['name']):
                    deleted_count += 1
            
            logger.info(f"Cleaned up {deleted_count} temporary files for process {process_id}")
            return deleted_count
            
        except Exception as e:
            logger.error(f"Error cleaning up temp files: {e}")
            return 0

# Global instance
minio_service = MinIOService()