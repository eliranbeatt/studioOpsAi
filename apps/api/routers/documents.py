"""
Enhanced Documents API Router

This router provides comprehensive document management functionality using
the enhanced DocumentUploadService with proper error handling, deduplication,
and atomic operations.
"""

from fastapi import APIRouter, HTTPException, UploadFile, File, Form, Depends, BackgroundTasks
from fastapi.responses import StreamingResponse
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from uuid import UUID
import logging

from database import get_db
from services.document_upload_service import document_upload_service
from services.observability_service import observability_service
from utils.error_handling import (
    create_http_exception, ErrorCategory, ErrorSeverity, FieldError,
    create_validation_error
)
from utils.validation import DocumentValidator, validate_and_raise

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/documents", tags=["documents"])

@router.post("/upload")
async def upload_document(
    file: UploadFile = File(...),
    project_id: Optional[str] = Form(None),
    user_id: Optional[str] = Form(None),
    db: Session = Depends(get_db)
):
    """
    Upload a single document with comprehensive error handling and validation
    
    Features:
    - Pre-upload validation with bilingual error messages
    - Atomic upload with database record creation
    - SHA256-based deduplication
    - Comprehensive validation
    - Automatic cleanup on failures
    - Background processing queue
    """
    
    try:
        # Pre-upload validation
        if not file.filename:
            raise create_validation_error([
                FieldError(
                    field="file",
                    message="File name is required",
                    message_he="שם הקובץ נדרש",
                    code="filename_required"
                )
            ])
        
        # Get file size if available
        file_size = 0
        if hasattr(file, 'size') and file.size:
            file_size = file.size
        elif file.file:
            # Try to get size from file object
            current_pos = file.file.tell()
            file.file.seek(0, 2)  # Seek to end
            file_size = file.file.tell()
            file.file.seek(current_pos)  # Restore position
        
        # Validate document parameters
        validate_and_raise(
            DocumentValidator.validate_document_upload,
            file.filename,
            file_size,
            file.content_type
        )
        
        result = await document_upload_service.upload_document(
            file=file,
            project_id=project_id,
            db=db,
            user_id=user_id
        )
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error in document upload: {e}")
        raise HTTPException(
            status_code=500,
            detail="An unexpected error occurred during upload"
        )

@router.post("/upload/batch")
async def upload_documents_batch(
    files: List[UploadFile] = File(...),
    project_id: Optional[str] = Form(None),
    user_id: Optional[str] = Form(None),
    db: Session = Depends(get_db)
):
    """
    Upload multiple documents in batch with individual error handling
    
    Each file is processed independently, so some uploads may succeed
    while others fail. The response includes detailed status for each file.
    """
    
    if len(files) > 10:  # Reasonable batch limit
        raise HTTPException(
            status_code=400,
            detail="Maximum 10 files allowed per batch upload"
        )
    
    trace_id = observability_service.create_trace(
        name="batch_document_upload",
        metadata={
            'file_count': len(files),
            'project_id': project_id,
            'user_id': user_id
        }
    )
    
    results = []
    successful_uploads = 0
    
    for i, file in enumerate(files):
        try:
            result = await document_upload_service.upload_document(
                file=file,
                project_id=project_id,
                db=db,
                user_id=user_id
            )
            
            results.append({
                "index": i,
                "filename": file.filename,
                "status": "success",
                "result": result
            })
            
            if not result.get("duplicate", False):
                successful_uploads += 1
                
        except HTTPException as e:
            results.append({
                "index": i,
                "filename": file.filename,
                "status": "error",
                "error": {
                    "code": e.status_code,
                    "message": e.detail
                }
            })
        except Exception as e:
            logger.error(f"Unexpected error uploading file {file.filename}: {e}")
            results.append({
                "index": i,
                "filename": file.filename,
                "status": "error",
                "error": {
                    "code": 500,
                    "message": "Unexpected error occurred"
                }
            })
    
    observability_service.create_span(
        trace_id=trace_id,
        name="batch_upload_completed",
        metadata={
            'total_files': len(files),
            'successful_uploads': successful_uploads,
            'errors': len(files) - successful_uploads
        }
    )
    
    return {
        "total_files": len(files),
        "successful_uploads": successful_uploads,
        "errors": len(files) - successful_uploads,
        "results": results,
        "trace_id": trace_id
    }

@router.get("/{document_id}")
async def get_document_info(
    document_id: str,
    db: Session = Depends(get_db)
):
    """
    Get detailed information about a document including processing status
    """
    
    try:
        return await document_upload_service.get_document_info(document_id, db)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting document info: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to retrieve document information"
        )

@router.delete("/{document_id}")
async def delete_document(
    document_id: str,
    db: Session = Depends(get_db)
):
    """
    Delete a document and clean up associated storage
    """
    
    try:
        return await document_upload_service.delete_document(document_id, db)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting document: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to delete document"
        )

@router.get("/{document_id}/download")
async def download_document(
    document_id: str,
    db: Session = Depends(get_db)
):
    """
    Download a document from storage
    """
    
    if not document_upload_service.is_available():
        raise HTTPException(
            status_code=503,
            detail="Document storage service is currently unavailable"
        )
    
    try:
        from models import Document
        
        # Get document record
        document = db.query(Document).filter(Document.id == document_id).first()
        if not document:
            raise HTTPException(status_code=404, detail="Document not found")
        
        # Get file from MinIO
        try:
            response = document_upload_service.minio_client.get_object(
                document_upload_service.bucket_name,
                document.storage_path
            )
            
            def generate():
                try:
                    for chunk in response.stream(8192):
                        yield chunk
                finally:
                    response.close()
                    response.release_conn()
            
            return StreamingResponse(
                generate(),
                media_type=document.mime_type or 'application/octet-stream',
                headers={
                    "Content-Disposition": f"attachment; filename={document.filename}"
                }
            )
            
        except Exception as e:
            logger.error(f"Failed to download document from storage: {e}")
            raise HTTPException(
                status_code=500,
                detail="Failed to retrieve document from storage"
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error downloading document: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to download document"
        )

@router.get("/")
async def list_documents(
    project_id: Optional[str] = None,
    document_type: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
    db: Session = Depends(get_db)
):
    """
    List documents with optional filtering
    """
    
    try:
        from models import Document
        from sqlalchemy import desc
        
        query = db.query(Document)
        
        # Apply filters
        if project_id:
            query = query.filter(Document.project_id == project_id)
        
        if document_type:
            query = query.filter(Document.type == document_type)
        
        # Apply pagination and ordering
        documents = query.order_by(desc(Document.created_at)).offset(offset).limit(limit).all()
        
        # Get total count for pagination
        total_count = query.count()
        
        return {
            "documents": [
                {
                    "id": doc.id,
                    "filename": doc.filename,
                    "mime_type": doc.mime_type,
                    "size_bytes": doc.size_bytes,
                    "type": doc.type,
                    "confidence": doc.confidence,
                    "project_id": doc.project_id,
                    "created_at": doc.created_at.isoformat()
                }
                for doc in documents
            ],
            "pagination": {
                "total": total_count,
                "limit": limit,
                "offset": offset,
                "has_more": offset + limit < total_count
            },
            "storage_available": document_upload_service.is_available()
        }
        
    except Exception as e:
        logger.error(f"Error listing documents: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to list documents"
        )

@router.get("/health")
async def get_storage_health():
    """
    Get storage service health status
    """
    
    try:
        is_available = document_upload_service.is_available()
        
        health_info = {
            "storage_available": is_available,
            "service": "MinIO",
            "buckets": {
                "documents": document_upload_service.bucket_name,
                "temp": document_upload_service.temp_bucket
            }
        }
        
        if is_available and document_upload_service.minio_client:
            try:
                # Get bucket info
                buckets = document_upload_service.minio_client.list_buckets()
                health_info["bucket_count"] = len(buckets)
                health_info["status"] = "healthy"
            except Exception as e:
                health_info["status"] = "degraded"
                health_info["error"] = str(e)
        else:
            health_info["status"] = "unavailable"
            health_info["error"] = "MinIO client not initialized"
        
        return health_info
        
    except Exception as e:
        logger.error(f"Error checking storage health: {e}")
        return {
            "storage_available": False,
            "status": "error",
            "error": str(e)
        }

@router.post("/{document_id}/reprocess")
async def reprocess_document(
    document_id: str,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    Reprocess a document through the ingestion pipeline
    """
    
    try:
        from models import Document
        
        # Verify document exists
        document = db.query(Document).filter(Document.id == document_id).first()
        if not document:
            raise HTTPException(status_code=404, detail="Document not found")
        
        # Queue for reprocessing
        trace_id = observability_service.create_trace(
            name="document_reprocessing",
            metadata={'document_id': document_id}
        )
        
        await document_upload_service._queue_for_processing(document_id, trace_id)
        
        return {
            "document_id": document_id,
            "message": "Document queued for reprocessing",
            "trace_id": trace_id
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error reprocessing document: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to queue document for reprocessing"
        )

@router.get("/stats/summary")
async def get_document_stats(
    project_id: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    Get document statistics and summary
    """
    
    try:
        from models import Document
        from sqlalchemy import func
        
        query = db.query(Document)
        
        if project_id:
            query = query.filter(Document.project_id == project_id)
        
        # Get basic stats
        total_documents = query.count()
        total_size = query.with_entities(func.sum(Document.size_bytes)).scalar() or 0
        
        # Get type distribution
        type_stats = db.query(
            Document.type,
            func.count(Document.id).label('count')
        ).group_by(Document.type)
        
        if project_id:
            type_stats = type_stats.filter(Document.project_id == project_id)
        
        type_distribution = {
            row.type or 'unknown': row.count 
            for row in type_stats.all()
        }
        
        return {
            "total_documents": total_documents,
            "total_size_bytes": total_size,
            "total_size_mb": round(total_size / (1024 * 1024), 2),
            "type_distribution": type_distribution,
            "storage_available": document_upload_service.is_available(),
            "project_id": project_id
        }
        
    except Exception as e:
        logger.error(f"Error getting document stats: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to get document statistics"
        )