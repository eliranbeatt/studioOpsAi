"""
Enhanced Document Upload and Processing Service

This service provides comprehensive document upload functionality with:
- MinIO client initialization with proper error handling
- Atomic document upload with database record creation
- File deduplication using SHA256 hashing
- Document processing queue for background tasks
- Comprehensive cleanup on upload failures
"""

import os
import io
import hashlib
import uuid
import logging
import asyncio
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
from pathlib import Path
import tempfile
import mimetypes

from fastapi import HTTPException, UploadFile
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from minio import Minio
from minio.error import S3Error

from models import Document, IngestEvent
from services.observability_service import observability_service

logger = logging.getLogger(__name__)

class DocumentUploadService:
    """Enhanced document upload service with comprehensive error handling and atomic operations"""
    
    def __init__(self):
        self.minio_client = None
        self.bucket_name = os.getenv('MINIO_DOCUMENTS_BUCKET', 'documents')
        self.temp_bucket = os.getenv('MINIO_TEMP_BUCKET', 'temp')
        self.max_file_size = int(os.getenv('MAX_FILE_SIZE_MB', '50')) * 1024 * 1024  # 50MB default
        self.allowed_mime_types = {
            'application/pdf',
            'image/jpeg',
            'image/png',
            'image/tiff',
            'text/plain',
            'application/msword',
            'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
            'application/vnd.ms-excel',
            'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        }
        
        # Initialize MinIO client with proper error handling
        self._init_minio_client()
        
        # Processing queue for background tasks
        self.processing_queue = asyncio.Queue()
        self._processing_task = None
    
    def _init_minio_client(self):
        """Initialize MinIO client with comprehensive error handling"""
        try:
            endpoint = os.getenv('MINIO_ENDPOINT', 'localhost:9000')
            access_key = os.getenv('MINIO_ACCESS_KEY', 'studioops')
            secret_key = os.getenv('MINIO_SECRET_KEY', 'studioops123')
            secure = os.getenv('MINIO_SECURE', 'false').lower() == 'true'
            
            if not access_key or not secret_key:
                raise ValueError("MinIO credentials not configured")
            
            self.minio_client = Minio(
                endpoint=endpoint,
                access_key=access_key,
                secret_key=secret_key,
                secure=secure
            )
            
            # Test connection and create buckets if needed
            self._ensure_buckets_exist()
            
            logger.info(f"MinIO client initialized successfully - endpoint: {endpoint}")
            
        except Exception as e:
            logger.error(f"Failed to initialize MinIO client: {e}")
            self.minio_client = None
            # Don't raise exception here - allow service to start in degraded mode
    
    def _ensure_buckets_exist(self):
        """Ensure required buckets exist"""
        if not self.minio_client:
            return
        
        try:
            buckets_to_create = [self.bucket_name, self.temp_bucket]
            
            for bucket in buckets_to_create:
                if not self.minio_client.bucket_exists(bucket):
                    self.minio_client.make_bucket(bucket)
                    logger.info(f"Created MinIO bucket: {bucket}")
                else:
                    logger.debug(f"MinIO bucket exists: {bucket}")
                    
        except S3Error as e:
            logger.error(f"Failed to ensure buckets exist: {e}")
            raise HTTPException(
                status_code=500,
                detail="Document storage service configuration error"
            )
    
    def is_available(self) -> bool:
        """Check if MinIO service is available"""
        if not self.minio_client:
            return False
        
        try:
            # Simple health check
            self.minio_client.list_buckets()
            return True
        except Exception as e:
            logger.warning(f"MinIO health check failed: {e}")
            return False
    
    async def upload_document(self, 
                            file: UploadFile, 
                            project_id: Optional[str] = None,
                            db: Session = None,
                            user_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Upload document with atomic database and storage operations
        
        Args:
            file: The uploaded file
            project_id: Optional project ID to associate with document
            db: Database session
            user_id: Optional user ID for audit trail
            
        Returns:
            Dict containing upload result with document_id, status, and metadata
        """
        
        if not self.is_available():
            raise HTTPException(
                status_code=503,
                detail="Document storage service is currently unavailable"
            )
        
        # Generate trace ID for observability
        trace_id = observability_service.create_trace(
            name="document_upload",
            metadata={
                'filename': file.filename,
                'content_type': file.content_type,
                'project_id': project_id,
                'user_id': user_id
            }
        )
        
        document_id = uuid.uuid4()  # Use UUID object, not string
        temp_storage_path = None
        
        try:
            # Step 1: Validate file
            await self._validate_file(file, trace_id)
            
            # Step 2: Read file content and calculate hash
            file_content = await file.read()
            file_hash = hashlib.sha256(file_content).hexdigest()
            
            observability_service.create_span(
                trace_id=trace_id,
                name="file_hash_calculated",
                metadata={
                    'file_size': len(file_content),
                    'sha256': file_hash[:16] + '...'  # Truncated for logging
                }
            )
            
            # Step 3: Check for existing document with same hash (deduplication)
            existing_doc = await self._check_duplicate(file_hash, db, trace_id)
            if existing_doc:
                return {
                    "document_id": existing_doc.id,
                    "filename": existing_doc.filename,
                    "size_bytes": existing_doc.size_bytes,
                    "message": "Document already exists (duplicate detected)",
                    "duplicate": True,
                    "existing_document": {
                        "id": existing_doc.id,
                        "filename": existing_doc.filename,
                        "created_at": existing_doc.created_at.isoformat(),
                        "project_id": existing_doc.project_id
                    },
                    "trace_id": trace_id
                }
            
            # Step 4: Upload to temporary location first
            temp_storage_path = f"temp/{str(document_id)}/{file.filename}"
            await self._upload_to_minio(file_content, temp_storage_path, file.content_type, trace_id)
            
            # Step 5: Create database record (atomic operation)
            document = await self._create_document_record(
                document_id=document_id,
                filename=file.filename,
                mime_type=file.content_type,
                size_bytes=len(file_content),
                content_hash=file_hash,
                project_id=project_id,
                temp_path=temp_storage_path,
                db=db,
                trace_id=trace_id
            )
            
            # Step 6: Move from temp to permanent location
            permanent_path = f"documents/{str(document_id)}/{file.filename}"
            await self._move_to_permanent_storage(temp_storage_path, permanent_path, trace_id)
            
            # Step 7: Update document record with permanent path
            document.path = permanent_path
            document.storage_path = permanent_path
            db.commit()
            
            # Step 8: Queue for background processing
            await self._queue_for_processing(str(document_id), trace_id)
            
            # Step 9: Log successful upload
            await self._log_ingest_event(
                document_id=str(document_id),
                stage="upload",
                status="ok",
                payload={"filename": file.filename, "size_bytes": len(file_content)},
                db=db
            )
            
            observability_service.create_span(
                trace_id=trace_id,
                name="upload_completed",
                metadata={
                    'document_id': document_id,
                    'final_path': permanent_path,
                    'queued_for_processing': True
                }
            )
            
            return {
                "document_id": str(document_id),
                "filename": file.filename,
                "size_bytes": len(file_content),
                "mime_type": file.content_type,
                "storage_path": permanent_path,
                "content_sha256": file_hash,
                "project_id": project_id,
                "message": "Document uploaded successfully",
                "duplicate": False,
                "queued_for_processing": True,
                "trace_id": trace_id
            }
            
        except Exception as e:
            # Comprehensive cleanup on failure
            await self._cleanup_failed_upload(
                document_id=str(document_id),
                temp_path=temp_storage_path,
                db=db,
                trace_id=trace_id,
                error=str(e)
            )
            
            logger.error(f"Document upload failed: {e}")
            observability_service.track_error(
                trace_id=trace_id,
                error_type="upload_error",
                error_message=str(e),
                context={
                    'document_id': document_id,
                    'filename': file.filename if file else 'unknown'
                }
            )
            
            raise HTTPException(
                status_code=500,
                detail=f"Document upload failed: {str(e)}"
            )
    
    async def _validate_file(self, file: UploadFile, trace_id: str):
        """Validate uploaded file"""
        
        # Check file size
        if hasattr(file, 'size') and file.size > self.max_file_size:
            raise HTTPException(
                status_code=413,
                detail=f"File too large. Maximum size: {self.max_file_size // (1024*1024)}MB"
            )
        
        # Check MIME type
        if file.content_type and file.content_type not in self.allowed_mime_types:
            # Try to detect MIME type from filename
            detected_type, _ = mimetypes.guess_type(file.filename)
            if detected_type not in self.allowed_mime_types:
                raise HTTPException(
                    status_code=415,
                    detail=f"Unsupported file type: {file.content_type or detected_type}"
                )
        
        # Check filename
        if not file.filename or len(file.filename.strip()) == 0:
            raise HTTPException(
                status_code=400,
                detail="Filename is required"
            )
        
        # Check for potentially dangerous filenames
        dangerous_chars = ['..', '/', '\\', '<', '>', ':', '"', '|', '?', '*']
        if any(char in file.filename for char in dangerous_chars):
            raise HTTPException(
                status_code=400,
                detail="Filename contains invalid characters"
            )
        
        observability_service.create_span(
            trace_id=trace_id,
            name="file_validated",
            metadata={
                'filename': file.filename,
                'content_type': file.content_type,
                'validation_passed': True
            }
        )
    
    async def _check_duplicate(self, file_hash: str, db: Session, trace_id: str) -> Optional[Document]:
        """Check for existing document with same hash"""
        
        try:
            existing_doc = db.query(Document).filter(
                Document.content_sha256 == file_hash
            ).first()
            
            if existing_doc:
                observability_service.create_span(
                    trace_id=trace_id,
                    name="duplicate_detected",
                    metadata={
                        'existing_document_id': existing_doc.id,
                        'existing_filename': existing_doc.filename,
                        'hash': file_hash[:16] + '...'
                    }
                )
            
            return existing_doc
            
        except Exception as e:
            logger.error(f"Error checking for duplicates: {e}")
            # Don't fail upload for duplicate check errors
            return None
    
    async def _upload_to_minio(self, file_content: bytes, storage_path: str, content_type: str, trace_id: str):
        """Upload file content to MinIO"""
        
        try:
            file_stream = io.BytesIO(file_content)
            
            self.minio_client.put_object(
                bucket_name=self.temp_bucket,
                object_name=storage_path,
                data=file_stream,
                length=len(file_content),
                content_type=content_type or 'application/octet-stream'
            )
            
            observability_service.create_span(
                trace_id=trace_id,
                name="minio_upload_completed",
                metadata={
                    'bucket': self.temp_bucket,
                    'path': storage_path,
                    'size_bytes': len(file_content)
                }
            )
            
        except S3Error as e:
            logger.error(f"MinIO upload failed: {e}")
            raise HTTPException(
                status_code=500,
                detail=f"File storage failed: {str(e)}"
            )
    
    async def _create_document_record(self, 
                                   document_id: uuid.UUID,
                                   filename: str,
                                   mime_type: str,
                                   size_bytes: int,
                                   content_hash: str,
                                   project_id: Optional[str],
                                   temp_path: str,
                                   db: Session,
                                   trace_id: str) -> Document:
        """Create document record in database"""
        
        try:
            # Detect document type from filename and content type
            doc_type = self._detect_document_type(filename, mime_type)
            
            # Convert project_id to UUID if provided
            project_uuid = None
            if project_id:
                try:
                    project_uuid = uuid.UUID(project_id)
                except ValueError:
                    # If project_id is not a valid UUID, set to None
                    project_uuid = None
            
            document = Document(
                id=str(document_id),  # Convert UUID to string
                filename=filename,
                mime_type=mime_type,
                size_bytes=size_bytes,
                project_id=str(project_uuid) if project_uuid else None,  # Convert UUID to string
                path=temp_path,  # Required path field
                storage_path=temp_path,  # Will be updated to permanent path later
                content_sha256=content_hash,
                type=doc_type,
                confidence=None,  # Will be set after processing
                language=None,    # Will be detected during processing
                version=1  # Initial version
            )
            
            db.add(document)
            db.flush()  # Get the ID without committing
            
            observability_service.create_span(
                trace_id=trace_id,
                name="document_record_created",
                metadata={
                    'document_id': document_id,
                    'detected_type': doc_type,
                    'project_id': project_id
                }
            )
            
            return document
            
        except IntegrityError as e:
            db.rollback()
            if 'content_sha256' in str(e):
                # This is a duplicate hash constraint violation
                # This shouldn't happen due to our duplicate check, but handle it gracefully
                raise HTTPException(
                    status_code=409,
                    detail="Document with identical content already exists"
                )
            else:
                raise HTTPException(
                    status_code=500,
                    detail=f"Database error: {str(e)}"
                )
        except Exception as e:
            db.rollback()
            raise HTTPException(
                status_code=500,
                detail=f"Failed to create document record: {str(e)}"
            )
    
    def _detect_document_type(self, filename: str, mime_type: str) -> str:
        """Detect document type from filename and MIME type"""
        
        filename_lower = filename.lower()
        
        # Check filename patterns
        if any(word in filename_lower for word in ['invoice', 'חשבונית']):
            return 'invoice'
        elif any(word in filename_lower for word in ['quote', 'quotation', 'הצעת מחיר']):
            return 'quote'
        elif any(word in filename_lower for word in ['receipt', 'קבלה']):
            return 'receipt'
        elif any(word in filename_lower for word in ['contract', 'חוזה']):
            return 'contract'
        elif any(word in filename_lower for word in ['spec', 'specification', 'מפרט']):
            return 'specification'
        elif any(word in filename_lower for word in ['plan', 'blueprint', 'תוכנית']):
            return 'blueprint'
        elif any(word in filename_lower for word in ['catalog', 'קטלוג']):
            return 'catalog'
        elif any(word in filename_lower for word in ['shipping', 'delivery', 'משלוח']):
            return 'shipping_quote'
        
        # Check MIME type patterns
        if mime_type:
            if mime_type.startswith('image/'):
                return 'image'
            elif mime_type == 'application/pdf':
                return 'pdf'
            elif 'spreadsheet' in mime_type or 'excel' in mime_type:
                return 'spreadsheet'
            elif 'word' in mime_type:
                return 'document'
        
        return 'other'
    
    async def _move_to_permanent_storage(self, temp_path: str, permanent_path: str, trace_id: str):
        """Move file from temporary to permanent storage"""
        
        try:
            from minio.commonconfig import CopySource
            
            # Create proper CopySource object
            copy_source = CopySource(self.temp_bucket, temp_path)
            
            # Copy from temp bucket to documents bucket
            self.minio_client.copy_object(
                bucket_name=self.bucket_name,
                object_name=permanent_path,
                source=copy_source
            )
            
            # Remove from temp bucket
            self.minio_client.remove_object(self.temp_bucket, temp_path)
            
            observability_service.create_span(
                trace_id=trace_id,
                name="moved_to_permanent_storage",
                metadata={
                    'temp_path': temp_path,
                    'permanent_path': permanent_path,
                    'bucket': self.bucket_name
                }
            )
            
        except S3Error as e:
            logger.error(f"Failed to move file to permanent storage: {e}")
            raise HTTPException(
                status_code=500,
                detail=f"Failed to finalize file storage: {str(e)}"
            )
    
    async def _queue_for_processing(self, document_id: str, trace_id: str):
        """Queue document for background processing"""
        
        try:
            processing_task = {
                'document_id': document_id,
                'trace_id': trace_id,
                'queued_at': datetime.utcnow().isoformat(),
                'priority': 'normal'
            }
            
            await self.processing_queue.put(processing_task)
            
            # Start processing task if not already running
            if self._processing_task is None or self._processing_task.done():
                self._processing_task = asyncio.create_task(self._process_queue())
            
            observability_service.create_span(
                trace_id=trace_id,
                name="queued_for_processing",
                metadata={
                    'document_id': document_id,
                    'queue_size': self.processing_queue.qsize()
                }
            )
            
        except Exception as e:
            logger.error(f"Failed to queue document for processing: {e}")
            # Don't fail the upload for queueing errors
    
    async def _process_queue(self):
        """Background task to process queued documents"""
        
        while True:
            try:
                # Get next task from queue (wait up to 60 seconds)
                task = await asyncio.wait_for(self.processing_queue.get(), timeout=60.0)
                
                document_id = task['document_id']
                trace_id = task['trace_id']
                
                logger.info(f"Processing queued document: {document_id}")
                
                # Import here to avoid circular imports
                from services.ingestion_service import ingestion_service
                
                # Process the document
                # Note: This would typically call the ingestion pipeline
                # For now, we'll just log the processing
                await self._process_document_async(document_id, trace_id)
                
                self.processing_queue.task_done()
                
            except asyncio.TimeoutError:
                # No tasks in queue, continue waiting
                continue
            except Exception as e:
                logger.error(f"Error processing document queue: {e}")
                # Continue processing other documents
                continue
    
    async def _process_document_async(self, document_id: str, trace_id: str):
        """Process a single document asynchronously"""
        
        try:
            # This is a placeholder for actual document processing
            # In a real implementation, this would:
            # 1. Download the document from MinIO
            # 2. Run it through the ingestion pipeline
            # 3. Extract text and metadata
            # 4. Update the document record with results
            
            await asyncio.sleep(1)  # Simulate processing time
            
            observability_service.create_span(
                trace_id=trace_id,
                name="document_processed_async",
                metadata={
                    'document_id': document_id,
                    'processing_status': 'completed'
                }
            )
            
            logger.info(f"Document {document_id} processed successfully")
            
        except Exception as e:
            logger.error(f"Failed to process document {document_id}: {e}")
            observability_service.track_error(
                trace_id=trace_id,
                error_type="async_processing_error",
                error_message=str(e),
                context={'document_id': document_id}
            )
    
    async def _cleanup_failed_upload(self, 
                                   document_id: str,
                                   temp_path: Optional[str],
                                   db: Session,
                                   trace_id: str,
                                   error: str):
        """Comprehensive cleanup on upload failure"""
        
        cleanup_actions = []
        
        try:
            # 1. Remove temporary file from MinIO if it exists
            if temp_path and self.minio_client:
                try:
                    self.minio_client.remove_object(self.temp_bucket, temp_path)
                    cleanup_actions.append("temp_file_removed")
                except Exception as e:
                    logger.warning(f"Failed to remove temp file {temp_path}: {e}")
            
            # 2. Remove document record from database if it exists
            if db:
                try:
                    # Document ID is a string in the database
                    document = db.query(Document).filter(Document.id == document_id).first()
                    if document:
                        db.delete(document)
                        db.commit()
                        cleanup_actions.append("database_record_removed")
                except Exception as e:
                    logger.warning(f"Failed to remove document record {document_id}: {e}")
                    try:
                        db.rollback()
                    except:
                        pass
            
            # 3. Log cleanup event
            if db:
                await self._log_ingest_event(
                    document_id=document_id,
                    stage="upload",
                    status="fail",
                    payload={
                        "error": error,
                        "cleanup_actions": cleanup_actions
                    },
                    db=db
                )
            
            observability_service.create_span(
                trace_id=trace_id,
                name="cleanup_completed",
                metadata={
                    'document_id': document_id,
                    'cleanup_actions': cleanup_actions,
                    'error': error
                }
            )
            
        except Exception as cleanup_error:
            logger.error(f"Cleanup failed for document {document_id}: {cleanup_error}")
            observability_service.track_error(
                trace_id=trace_id,
                error_type="cleanup_error",
                error_message=str(cleanup_error),
                context={
                    'document_id': document_id,
                    'original_error': error
                }
            )
    
    async def _log_ingest_event(self, 
                              document_id: str,
                              stage: str,
                              status: str,
                              payload: Dict[str, Any],
                              db: Session):
        """Log ingestion event to database"""
        
        try:
            event = IngestEvent(
                document_id=document_id,
                stage=stage,
                status=status,
                payload_jsonb=payload,
                created_at=datetime.utcnow()
            )
            
            db.add(event)
            db.commit()
            
        except Exception as e:
            logger.error(f"Failed to log ingest event: {e}")
            # Don't fail the main operation for logging errors
            try:
                db.rollback()
            except:
                pass
    
    async def get_document_info(self, document_id: str, db: Session) -> Dict[str, Any]:
        """Get document information and processing status"""
        
        try:
            # Document ID is a string in the database
            document = db.query(Document).filter(Document.id == document_id).first()
            if not document:
                raise HTTPException(status_code=404, detail="Document not found")
            
            # Get processing events
            events = db.query(IngestEvent).filter(
                IngestEvent.document_id == document_id
            ).order_by(IngestEvent.created_at.desc()).limit(10).all()
            
            return {
                "document": {
                    "id": str(document.id),
                    "filename": document.filename,
                    "mime_type": document.mime_type,
                    "size_bytes": document.size_bytes,
                    "type": document.type,
                    "confidence": document.confidence,
                    "project_id": str(document.project_id) if document.project_id else None,
                    "storage_path": document.storage_path,
                    "content_sha256": document.content_sha256,
                    "created_at": document.created_at.isoformat() if document.created_at else None
                },
                "processing_events": [
                    {
                        "stage": event.stage,
                        "status": event.status,
                        "payload": event.payload_jsonb,
                        "created_at": event.created_at.isoformat()
                    }
                    for event in events
                ],
                "storage_available": self.is_available()
            }
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Failed to get document info: {e}")
            raise HTTPException(
                status_code=500,
                detail=f"Failed to retrieve document information: {str(e)}"
            )
    
    async def delete_document(self, document_id: str, db: Session) -> Dict[str, Any]:
        """Delete a document and clean up associated storage"""
        
        try:
            # Get document record (document ID is a string)
            document = db.query(Document).filter(Document.id == document_id).first()
            if not document:
                raise HTTPException(status_code=404, detail="Document not found")
            
            # Create trace for observability
            trace_id = observability_service.create_trace(
                name="document_deletion",
                metadata={'document_id': document_id}
            )
            
            cleanup_actions = []
            
            # Remove from MinIO storage
            if self.is_available() and document.storage_path:
                try:
                    self.minio_client.remove_object(self.bucket_name, document.storage_path)
                    cleanup_actions.append("storage_file_removed")
                    logger.info(f"Removed file from storage: {document.storage_path}")
                except S3Error as e:
                    logger.warning(f"Failed to remove storage file: {e}")
                    cleanup_actions.append("storage_removal_failed")
            
            # Remove database record
            db.delete(document)
            db.commit()
            cleanup_actions.append("database_record_removed")
            
            # Log deletion event
            await self._log_ingest_event(
                document_id=document_id,
                stage="delete",
                status="ok",
                payload={"filename": document.filename, "cleanup_actions": cleanup_actions},
                db=db
            )
            
            observability_service.create_span(
                trace_id=trace_id,
                name="document_deleted",
                metadata={
                    'document_id': document_id,
                    'cleanup_actions': cleanup_actions
                }
            )
            
            return {
                "document_id": document_id,
                "filename": document.filename,
                "message": "Document deleted successfully",
                "cleanup_actions": cleanup_actions,
                "trace_id": trace_id
            }
            
        except HTTPException:
            raise
        except Exception as e:
            db.rollback()
            logger.error(f"Failed to delete document: {e}")
            raise HTTPException(
                status_code=500,
                detail=f"Failed to delete document: {str(e)}"
            )

# Global instance
document_upload_service = DocumentUploadService()