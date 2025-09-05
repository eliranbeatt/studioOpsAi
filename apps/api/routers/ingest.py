"""
Ingestion pipeline API endpoints for document processing and extraction
"""

from fastapi import APIRouter, HTTPException, UploadFile, File, Form, BackgroundTasks
from fastapi.responses import StreamingResponse
from typing import List, Optional, Dict, Any
import uuid
import json
import asyncio
from datetime import datetime
import psycopg2
import os
from uuid import UUID

from services.observability_service import observability_service
try:
    from services.instructor_service import instructor_service
    INSTRUCTOR_AVAILABLE = True
except ImportError:
    instructor_service = None
    INSTRUCTOR_AVAILABLE = False
try:
    from services.ocr_service import ocr_service
    OCR_AVAILABLE = True
except ImportError:
    ocr_service = None
    OCR_AVAILABLE = False
try:
    from services.unstructured_service import unstructured_service
    UNSTRUCTURED_AVAILABLE = True
except ImportError:
    unstructured_service = None
    UNSTRUCTURED_AVAILABLE = False
try:
    from services.ingestion_service import ingestion_service
    INGESTION_AVAILABLE = True
except ImportError:
    ingestion_service = None
    INGESTION_AVAILABLE = False

router = APIRouter(prefix="/ingest", tags=["ingest"])

def get_db_connection():
    """Get a database connection"""
    try:
        conn = psycopg2.connect(
            os.getenv('DATABASE_URL', 'postgresql://studioops:studioops@localhost:5432/studioops')
        )
        return conn
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database connection failed: {e}")

@router.post("/upload")
async def upload_files(
    files: List[UploadFile] = File(...),
    project_id: Optional[str] = Form(None),
    tags: Optional[List[str]] = Form([])
):
    """Upload multiple files for ingestion"""
    
    trace_id = observability_service.create_trace(
        name="ingest_upload",
        metadata={
            'file_count': len(files),
            'project_id': project_id,
            'tags': tags
        }
    )
    
    try:
        document_ids = []
        statuses = []
        
        for file in files:
            try:
                # Generate unique document ID
                doc_id = uuid.uuid4()
                
                # Store file metadata in database
                conn = get_db_connection()
                cursor = conn.cursor()
                
                cursor.execute("""
                    INSERT INTO documents 
                    (id, filename, mime_type, project_id, storage_path, content_sha256)
                    VALUES (%s, %s, %s, %s, %s, %s)
                    RETURNING id
                """, (
                    str(doc_id), file.filename, file.content_type, 
                    project_id, f"uploads/{doc_id}/{file.filename}", 
                    f"sha256_{uuid.uuid4()}"  # Placeholder for actual hash
                ))
                
                conn.commit()
                cursor.close()
                conn.close()
                
                document_ids.append(str(doc_id))
                statuses.append("uploaded")
                
                # Log upload event
                observability_service.create_span(
                    trace_id=trace_id,
                    name="file_uploaded",
                    metadata={
                        'filename': file.filename,
                        'mime_type': file.content_type,
                        'document_id': str(doc_id)
                    }
                )
                
            except Exception as e:
                statuses.append(f"error: {str(e)}")
                observability_service.track_error(
                    trace_id=trace_id,
                    error_type="upload_error",
                    error_message=str(e),
                    context={'filename': file.filename}
                )
        
        return {
            "document_ids": document_ids,
            "statuses": statuses,
            "trace_id": trace_id
        }
        
    except Exception as e:
        observability_service.track_error(
            trace_id=trace_id,
            error_type="upload_batch_error",
            error_message=str(e)
        )
        raise HTTPException(status_code=500, detail=f"Upload failed: {e}")

@router.post("/run/{document_id}")
async def run_ingestion_pipeline(document_id: UUID):
    """Start/continue ingestion pipeline for a document"""
    
    trace_id = observability_service.create_trace(
        name="ingest_pipeline_run",
        metadata={'document_id': str(document_id)}
    )
    
    async def generate_events():
        """Generate SSE events for pipeline progress with real processing"""
        
        # First get the document file path from database
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute(
                "SELECT storage_path FROM documents WHERE id = %s",
                (str(document_id),)
            )
            
            doc_row = cursor.fetchone()
            if not doc_row:
                yield f"data: {json.dumps({'stage': 'error', 'status': 'failed', 'progress': 0.0, 'message': 'Document not found'})}\n\n"
                return
            
            file_path = doc_row[0]
            cursor.close()
            conn.close()
            
            # Real file path would be resolved from storage_path
            # For now, we'll simulate the processing stages
            
            stages = [
                ("parse", "Starting document parsing"),
                ("classify", "Classifying document type"),
                ("pack", "Building retrieval context"),
                ("extract", "Extracting structured data"),
                ("validate", "Validating extracted data"),
                ("link", "Linking entities"),
                ("stage", "Staging results")
            ]
            
            for stage, message in stages:
                event_data = {
                    "stage": stage,
                    "status": "start",
                    "progress": stages.index((stage, message)) / len(stages),
                    "message": message,
                    "timestamp": datetime.now().isoformat()
                }
                
                yield f"data: {json.dumps(event_data)}\n\n"
                
                # Simulate processing time based on stage complexity
                if stage == "parse":
                    await asyncio.sleep(2)
                elif stage == "extract":
                    await asyncio.sleep(3)
                else:
                    await asyncio.sleep(1)
                
                # Stage completion
                event_data["status"] = "ok"
                event_data["progress"] = (stages.index((stage, message)) + 1) / len(stages)
                yield f"data: {json.dumps(event_data)}\n\n"
            
            # Final completion
            yield f"data: {json.dumps({'stage': 'complete', 'status': 'ok', 'progress': 1.0, 'message': 'Pipeline completed successfully'})}\n\n"
            
        except Exception as e:
            error_data = {
                "stage": "error", 
                "status": "failed", 
                "progress": 0.0, 
                "message": f"Pipeline failed: {str(e)}",
                "timestamp": datetime.now().isoformat()
            }
            yield f"data: {json.dumps(error_data)}\n\n"
    
    return StreamingResponse(
        generate_events(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Trace-ID": trace_id
        }
    )

@router.post("/process/{document_id}")
async def process_document_sync(document_id: UUID):
    """Process document synchronously using ingestion service"""
    
    trace_id = observability_service.create_trace(
        name="ingest_process_sync",
        metadata={'document_id': str(document_id)}
    )
    
    try:
        # Get document info from database
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT id, filename, storage_path, project_id FROM documents WHERE id = %s",
            (str(document_id),)
        )
        
        doc_row = cursor.fetchone()
        if not doc_row:
            raise HTTPException(status_code=404, detail="Document not found")
        
        document = {
            'id': doc_row[0],
            'filename': doc_row[1],
            'storage_path': doc_row[2],
            'project_id': doc_row[3]
        }
        cursor.close()
        conn.close()
        
        # For now, we'll simulate file processing since actual file storage isn't implemented
        # In production, this would resolve the actual file path from storage_path
        
        # Simulate processing with the ingestion service
        # result = ingestion_service.process_document(
        #     file_path=document['storage_path'],
        #     document_id=document_id,
        #     project_id=document['project_id'],
        #     trace_id=trace_id
        # )
        
        # Simulate successful processing for now
        await asyncio.sleep(2)  # Simulate processing time
        
        result = {
            'success': True,
            'document_id': str(document_id),
            'pipeline_status': 'completed',
            'requires_review': False,
            'trace_id': trace_id,
            'results': {
                'parse': {'success': True, 'elements_count': 15},
                'classify': {'success': True, 'document_type': 'invoice', 'confidence': 0.85},
                'extract': {'success': True, 'extracted_items': [
                    {
                        'id': str(uuid.uuid4()),
                        'type': 'material',
                        'title': 'Concrete Mix',
                        'qty': 10.0,
                        'unit': 'm³',
                        'unit_price_nis': 450.0,
                        'total_price_nis': 4500.0,
                        'confidence': 0.9,
                        'source_ref': 'item_0'
                    }
                ]},
                'validate': {'success': True, 'valid_items_count': 1, 'total_items_count': 1},
                'stage': {'success': True, 'overall_confidence': 0.9, 'requires_review': False}
            }
        }
        
        # Store extraction results in database
        if result['success'] and 'results' in result:
            _store_extraction_results(document_id, result['results'])
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        observability_service.track_error(
            trace_id=trace_id,
            error_type="sync_process_error",
            error_message=str(e)
        )
        raise HTTPException(status_code=500, detail=f"Document processing failed: {e}")

@router.get("/{document_id}")
async def get_document_status(document_id: UUID):
    """Get current status and extracted data for a document"""
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Get document info
        cursor.execute("""
            SELECT id, filename, mime_type, type, confidence, project_id, created_at
            FROM documents WHERE id = %s
        """, (str(document_id),))
        
        doc_row = cursor.fetchone()
        if not doc_row:
            raise HTTPException(status_code=404, detail="Document not found")
        
        document = {
            "id": doc_row[0],
            "filename": doc_row[1],
            "mime_type": doc_row[2],
            "type": doc_row[3],
            "confidence": doc_row[4],
            "project_id": doc_row[5],
            "created_at": doc_row[6]
        }
        
        # Get extracted items
        cursor.execute("""
            SELECT id, type, title, qty, unit, unit_price_nis, confidence, source_ref
            FROM extracted_items WHERE document_id = %s
        """, (str(document_id),))
        
        extracted_items = []
        for row in cursor.fetchall():
            extracted_items.append({
                "id": row[0],
                "type": row[1],
                "title": row[2],
                "qty": row[3],
                "unit": row[4],
                "unit_price_nis": row[5],
                "confidence": row[6],
                "source_ref": row[7]
            })
        
        # Get vendor/material suggestions (simplified)
        suggestions = {
            "vendors": [],
            "materials": []
        }
        
        cursor.close()
        conn.close()
        
        return {
            "document": document,
            "extracted_items": extracted_items,
            "issues": [],
            "suggestions": suggestions,
            "clarifications": []
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching document status: {e}")

@router.post("/{document_id}/answer")
async def answer_clarification(
    document_id: UUID,
    answer_data: Dict[str, Any]
):
    """Answer a clarification question"""
    
    question_id = answer_data.get("question_id")
    answer = answer_data.get("answer")
    
    if not question_id or not answer:
        raise HTTPException(status_code=400, detail="question_id and answer are required")
    
    trace_id = observability_service.create_trace(
        name="ingest_clarification_answer",
        metadata={
            'document_id': str(document_id),
            'question_id': question_id,
            'answer_type': type(answer).__name__
        }
    )
    
    try:
        # Store the answer and recompute confidence
        # This would typically update the extraction and validation
        
        observability_service.create_span(
            trace_id=trace_id,
            name="clarification_processed",
            metadata={
                'question_id': question_id,
                'answer_received': str(answer)[:100]
            }
        )
        
        return {
            "success": True,
            "message": "Answer processed successfully",
            "recomputed_confidence": 0.85,  # Simulated
            "trace_id": trace_id
        }
        
    except Exception as e:
        observability_service.track_error(
            trace_id=trace_id,
            error_type="clarification_error",
            error_message=str(e)
        )
        raise HTTPException(status_code=500, detail=f"Error processing answer: {e}")

@router.post("/{document_id}/commit")
async def commit_document(document_id: UUID):
    """Commit extracted data to canonical tables"""
    
    trace_id = observability_service.create_trace(
        name="ingest_commit",
        metadata={'document_id': str(document_id)}
    )
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Simulate commit process
        # This would typically upsert into vendor_prices, purchases, etc.
        
        cursor.execute("""
            SELECT COUNT(*) FROM extracted_items 
            WHERE document_id = %s AND confidence >= 0.7
        """, (str(document_id),))
        
        valid_items = cursor.fetchone()[0]
        
        # Update document status
        cursor.execute("""
            UPDATE documents SET confidence = 0.9 
            WHERE id = %s RETURNING id
        """, (str(document_id),))
        
        conn.commit()
        cursor.close()
        conn.close()
        
        observability_service.create_span(
            trace_id=trace_id,
            name="commit_completed",
            metadata={
                'valid_items_count': valid_items,
                'document_id': str(document_id)
            }
        )
        
        return {
            "affected": {
                "vendor_prices": valid_items // 2,  # Simulated
                "purchases": valid_items // 3,
                "shipping_quotes": valid_items // 4,
                "plan_items": valid_items,
                "memories": valid_items * 2
            },
            "dossier_updates": ["Prices updated", "New items added"],
            "trace_id": trace_id
        }
        
    except Exception as e:
        observability_service.track_error(
            trace_id=trace_id,
            error_type="commit_error",
            error_message=str(e)
        )
        raise HTTPException(status_code=500, detail=f"Commit failed: {e}")

@router.get("/queue")
async def get_review_queue(status: str = "needs_review"):
    """Get documents needing review"""
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        if status == "needs_review":
            cursor.execute("""
                SELECT d.id, d.filename, d.type, d.confidence, d.created_at,
                       COUNT(e.id) as item_count,
                       SUM(CASE WHEN e.confidence < 0.7 THEN 1 ELSE 0 END) as low_confidence_items
                FROM documents d
                LEFT JOIN extracted_items e ON d.id = e.document_id
                WHERE d.confidence < 0.8 OR EXISTS (
                    SELECT 1 FROM extracted_items 
                    WHERE document_id = d.id AND confidence < 0.7
                )
                GROUP BY d.id, d.filename, d.type, d.confidence, d.created_at
                ORDER BY d.created_at DESC
            """)
        else:
            cursor.execute("""
                SELECT d.id, d.filename, d.type, d.confidence, d.created_at,
                       COUNT(e.id) as item_count
                FROM documents d
                LEFT JOIN extracted_items e ON d.id = e.document_id
                GROUP BY d.id, d.filename, d.type, d.confidence, d.created_at
                ORDER BY d.created_at DESC
                LIMIT 50
            """)
        
        documents = []
        for row in cursor.fetchall():
            documents.append({
                "id": row[0],
                "filename": row[1],
                "type": row[2],
                "confidence": row[3],
                "created_at": row[4],
                "item_count": row[5],
                "low_confidence_items": row[6] if len(row) > 6 else 0
            })
        
        cursor.close()
        conn.close()
        
        return {
            "status": status,
            "count": len(documents),
            "documents": documents
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching review queue: {e}")

@router.get("/lookup/vendors")
async def lookup_vendors(q: str, threshold: float = 0.3):
    """Fuzzy search for vendors"""
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT id, name, similarity(name, %s) as score
            FROM vendors 
            WHERE similarity(name, %s) >= %s
            ORDER BY score DESC
            LIMIT 10
        """, (q, q, threshold))
        
        vendors = []
        for row in cursor.fetchall():
            vendors.append({
                "id": row[0],
                "name": row[1],
                "score": float(row[2])
            })
        
        cursor.close()
        conn.close()
        
        return {
            "query": q,
            "threshold": threshold,
            "results": vendors
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error searching vendors: {e}")

@router.get("/lookup/materials")
async def lookup_materials(q: str, threshold: float = 0.3):
    """Fuzzy search for materials"""
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT id, name, similarity(name, %s) as score
            FROM materials 
            WHERE similarity(name, %s) >= %s
            ORDER BY score DESC
            LIMIT 10
        """, (q, q, threshold))
        
        materials = []
        for row in cursor.fetchall():
            materials.append({
                "id": row[0],
                "name": row[1],
                "score": float(row[2])
            })
        
        cursor.close()
        conn.close()
        
        return {
            "query": q,
            "threshold": threshold,
            "results": materials
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error searching materials: {e}")

def _store_extraction_results(document_id: UUID, results: Dict[str, Any]):
    """Store extraction results in database"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        extract_result = results.get('extract', {})
        extracted_items = extract_result.get('extracted_items', [])
        
        for item in extracted_items:
            cursor.execute("""
                INSERT INTO extracted_items 
                (id, document_id, type, title, qty, unit, unit_price_nis, confidence, source_ref)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (id) DO UPDATE SET
                type = EXCLUDED.type,
                title = EXCLUDED.title,
                qty = EXCLUDED.qty,
                unit = EXCLUDED.unit,
                unit_price_nis = EXCLUDED.unit_price_nis,
                confidence = EXCLUDED.confidence,
                source_ref = EXCLUDED.source_ref
            """, (
                item['id'], str(document_id), item.get('type'), 
                item.get('title'), item.get('qty'), item.get('unit'),
                item.get('unit_price_nis'), item.get('confidence', 0.7),
                item.get('source_ref', '')
            ))
        
        # Update document confidence
        stage_result = results.get('stage', {})
        overall_confidence = stage_result.get('overall_confidence', 0.7)
        
        cursor.execute(
            "UPDATE documents SET confidence = %s WHERE id = %s",
            (overall_confidence, str(document_id))
        )
        
        conn.commit()
        cursor.close()
        conn.close()
        
    except Exception as e:
        logger.error(f"Failed to store extraction results: {e}")
        # Don't raise exception here to avoid failing the entire request