"""Unstructured.io document parsing API endpoints"""

from fastapi import APIRouter, UploadFile, File, HTTPException, BackgroundTasks
from typing import List, Optional, Dict, Any
import tempfile
import os
from pathlib import Path
import json

from services.unstructured_service import unstructured_service
from services.observability_service import observability_service

router = APIRouter(prefix="/unstructured", tags=["unstructured"])

@router.post("/parse-document")
async def parse_document(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    strategy: str = "auto",
    languages: Optional[List[str]] = None,
    chunking_strategy: str = "by_title",
    extract_entities: bool = False
):
    """Parse document using Unstructured.io with intelligent processing"""
    
    if not file.filename:
        raise HTTPException(status_code=400, detail="Filename required")
    
    file_ext = Path(file.filename).suffix.lower()
    if file_ext not in unstructured_service.supported_extensions:
        raise HTTPException(
            status_code=400, 
            detail=f"Unsupported file type. Supported: {', '.join(unstructured_service.supported_extensions)}"
        )
    
    # Create trace for observability
    trace_id = observability_service.create_trace(
        name="unstructured_document_parsing",
        metadata={
            'filename': file.filename,
            'strategy': strategy,
            'languages': languages,
            'chunking_strategy': chunking_strategy,
            'file_size': file.size
        }
    )
    
    try:
        # Create temporary file
        with tempfile.NamedTemporaryFile(suffix=file_ext, delete=False) as tmp:
            input_path = tmp.name
            content = await file.read()
            tmp.write(content)
        
        # Parse document
        result = unstructured_service.parse_document(
            input_path, 
            strategy=strategy,
            languages=languages,
            chunking_strategy=chunking_strategy
        )
        
        # Extract entities if requested
        if extract_entities and result['success']:
            entities = unstructured_service.extract_entities(input_path)
            result['extracted_entities'] = entities
        
        # Track parsing operation
        observability_service.create_span(
            trace_id=trace_id,
            name="document_parsing",
            metadata={
                'input_path': input_path,
                'elements_count': result.get('elements_count', 0),
                'chunks_count': result.get('chunks_count', 0),
                'success': result.get('success', False)
            }
        )
        
        if not result.get('success'):
            raise HTTPException(
                status_code=500, 
                detail=f"Document parsing failed: {result.get('error')}"
            )
        
        # Cleanup function
        def cleanup_files():
            try:
                os.unlink(input_path)
            except Exception:
                pass
        
        background_tasks.add_task(cleanup_files)
        
        return result
        
    except Exception as e:
        observability_service.track_error(
            trace_id=trace_id,
            error_type=type(e).__name__,
            error_message=str(e),
            context={'filename': file.filename}
        )
        raise HTTPException(status_code=500, detail=f"Document parsing error: {e}")

@router.post("/extract-tables")
async def extract_tables_from_document(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...)
):
    """Extract tables from document with enhanced recognition"""
    
    if not file.filename:
        raise HTTPException(status_code=400, detail="Filename required")
    
    file_ext = Path(file.filename).suffix.lower()
    supported_for_tables = {'.pdf', '.docx', '.pptx', '.xlsx'}
    
    if file_ext not in supported_for_tables:
        raise HTTPException(
            status_code=400, 
            detail=f"Table extraction not supported for {file_ext}. Supported: {', '.join(supported_for_tables)}"
        )
    
    trace_id = observability_service.create_trace(
        name="table_extraction",
        metadata={'filename': file.filename, 'file_size': file.size}
    )
    
    try:
        with tempfile.NamedTemporaryFile(suffix=file_ext, delete=False) as tmp:
            input_path = tmp.name
            content = await file.read()
            tmp.write(content)
        
        tables = unstructured_service.extract_tables(input_path)
        
        observability_service.create_span(
            trace_id=trace_id,
            name="table_extraction_processing",
            metadata={
                'input_path': input_path,
                'tables_found': len(tables),
                'file_type': file_ext
            }
        )
        
        def cleanup_files():
            try:
                os.unlink(input_path)
            except Exception:
                pass
        
        background_tasks.add_task(cleanup_files)
        
        return {
            'success': True,
            'tables_found': len(tables),
            'tables': tables,
            'file_info': {
                'filename': file.filename,
                'type': file_ext,
                'size': file.size
            }
        }
        
    except Exception as e:
        observability_service.track_error(
            trace_id=trace_id,
            error_type=type(e).__name__,
            error_message=str(e)
        )
        raise HTTPException(status_code=500, detail=f"Table extraction error: {e}")

@router.post("/extract-entities")
async def extract_entities_from_document(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    entity_types: Optional[List[str]] = None
):
    """Extract entities (dates, prices, emails, etc.) from document"""
    
    if not file.filename:
        raise HTTPException(status_code=400, detail="Filename required")
    
    trace_id = observability_service.create_trace(
        name="entity_extraction",
        metadata={
            'filename': file.filename,
            'entity_types': entity_types,
            'file_size': file.size
        }
    )
    
    try:
        with tempfile.NamedTemporaryFile(suffix=Path(file.filename).suffix, delete=False) as tmp:
            input_path = tmp.name
            content = await file.read()
            tmp.write(content)
        
        entities = unstructured_service.extract_entities(input_path, entity_types)
        
        observability_service.create_span(
            trace_id=trace_id,
            name="entity_extraction_processing",
            metadata={
                'input_path': input_path,
                'entities_found': sum(len(v) for v in entities.values()),
                'entity_types_extracted': list(entities.keys())
            }
        )
        
        def cleanup_files():
            try:
                os.unlink(input_path)
            except Exception:
                pass
        
        background_tasks.add_task(cleanup_files)
        
        return {
            'success': True,
            'entities': entities,
            'total_entities': sum(len(v) for v in entities.values()),
            'file_info': {
                'filename': file.filename,
                'size': file.size
            }
        }
        
    except Exception as e:
        observability_service.track_error(
            trace_id=trace_id,
            error_type=type(e).__name__,
            error_message=str(e)
        )
        raise HTTPException(status_code=500, detail=f"Entity extraction error: {e}")

@router.post("/validate-structure")
async def validate_document_structure(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...)
):
    """Validate document structure and extract key sections"""
    
    if not file.filename:
        raise HTTPException(status_code=400, detail="Filename required")
    
    trace_id = observability_service.create_trace(
        name="document_structure_validation",
        metadata={'filename': file.filename, 'file_size': file.size}
    )
    
    try:
        with tempfile.NamedTemporaryFile(suffix=Path(file.filename).suffix, delete=False) as tmp:
            input_path = tmp.name
            content = await file.read()
            tmp.write(content)
        
        result = unstructured_service.validate_document_structure(input_path)
        
        observability_service.create_span(
            trace_id=trace_id,
            name="structure_validation",
            metadata={
                'input_path': input_path,
                'success': result.get('success', False),
                'sections_found': result.get('document_structure', {}).get('total_sections', 0)
            }
        )
        
        def cleanup_files():
            try:
                os.unlink(input_path)
            except Exception:
                pass
        
        background_tasks.add_task(cleanup_files)
        
        if not result.get('success'):
            raise HTTPException(
                status_code=500, 
                detail=f"Structure validation failed: {result.get('error')}"
            )
        
        return result
        
    except Exception as e:
        observability_service.track_error(
            trace_id=trace_id,
            error_type=type(e).__name__,
            error_message=str(e)
        )
        raise HTTPException(status_code=500, detail=f"Structure validation error: {e}")

@router.get("/supported-formats")
async def get_supported_formats():
    """Get list of supported file formats"""
    return {
        'supported_extensions': sorted(list(unstructured_service.supported_extensions)),
        'table_extraction_supported': ['.pdf', '.docx', '.pptx', '.xlsx'],
        'image_formats': ['.png', '.jpg', '.jpeg', '.tiff', '.bmp']
    }

@router.post("/batch-process")
async def batch_process_documents(
    input_directory: str,
    output_directory: str,
    strategy: str = "auto",
    languages: Optional[List[str]] = None
):
    """Batch process all documents in a directory"""
    
    if not os.path.isdir(input_directory):
        raise HTTPException(status_code=400, detail="Input directory not found")
    
    trace_id = observability_service.create_trace(
        name="batch_document_processing",
        metadata={
            'input_directory': input_directory,
            'output_directory': output_directory,
            'strategy': strategy,
            'languages': languages
        }
    )
    
    try:
        results = []
        supported_exts = unstructured_service.supported_extensions
        
        for file_path in Path(input_directory).iterdir():
            if file_path.suffix.lower() in supported_exts and file_path.is_file():
                result = unstructured_service.parse_document(
                    str(file_path), 
                    strategy=strategy,
                    languages=languages
                )
                
                results.append({
                    'file_path': str(file_path),
                    'file_name': file_path.name,
                    'success': result.get('success', False),
                    'elements_count': result.get('elements_count', 0),
                    'error': result.get('error')
                })
        
        observability_service.create_span(
            trace_id=trace_id,
            name="batch_processing_complete",
            metadata={
                'total_files_processed': len(results),
                'successful': len([r for r in results if r['success']]),
                'failed': len([r for r in results if not r['success']])
            }
        )
        
        return {
            'total_processed': len(results),
            'successful': len([r for r in results if r['success']]),
            'failed': len([r for r in results if not r['success']]),
            'results': results
        }
        
    except Exception as e:
        observability_service.track_error(
            trace_id=trace_id,
            error_type=type(e).__name__,
            error_message=str(e)
        )
        raise HTTPException(status_code=500, detail=f"Batch processing error: {e}")