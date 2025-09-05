"""OCR API endpoints for Hebrew document processing"""

from fastapi import APIRouter, UploadFile, File, HTTPException, BackgroundTasks
from fastapi.responses import FileResponse
from typing import List, Optional
import tempfile
import os
from pathlib import Path
import uuid
import shutil

from services.ocr_service import ocr_service
from services.observability_service import observability_service

router = APIRouter(prefix="/ocr", tags=["ocr"])

@router.post("/process-pdf")
async def process_pdf_with_ocr(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    languages: Optional[List[str]] = None,
    keep_output: bool = False
):
    """Process PDF with OCR (Hebrew supported)"""
    
    if not file.filename or not file.filename.lower().endswith('.pdf'):
        raise HTTPException(status_code=400, detail="PDF file required")
    
    # Create trace for observability
    trace_id = observability_service.create_trace(
        name="ocr_pdf_processing",
        metadata={
            'filename': file.filename,
            'languages': languages or ['heb', 'eng'],
            'file_size': file.size
        }
    )
    
    try:
        # Create temporary input file
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as tmp:
            input_path = tmp.name
            content = await file.read()
            tmp.write(content)
        
        # Generate output path
        output_filename = f"ocr_{Path(file.filename).stem}.pdf"
        output_dir = tempfile.mkdtemp()
        output_path = os.path.join(output_dir, output_filename)
        
        # Process with OCR
        result = ocr_service.process_pdf_with_ocr(
            input_path, 
            output_path, 
            languages
        )
        
        # Track OCR operation
        observability_service.create_span(
            trace_id=trace_id,
            name="ocr_processing",
            metadata={
                'input_path': input_path,
                'output_path': output_path,
                'result': result
            }
        )
        
        if not result.get('success'):
            raise HTTPException(
                status_code=500, 
                detail=f"OCR processing failed: {result.get('error')}"
            )
        
        # Cleanup function
        def cleanup_files():
            try:
                os.unlink(input_path)
                if not keep_output:
                    shutil.rmtree(output_dir, ignore_errors=True)
            except Exception as e:
                pass
        
        background_tasks.add_task(cleanup_files)
        
        return {
            'success': True,
            'output_filename': output_filename,
            'download_url': f"/ocr/download/{Path(output_path).name}",
            'result': result
        }
        
    except Exception as e:
        observability_service.track_error(
            trace_id=trace_id,
            error_type=type(e).__name__,
            error_message=str(e),
            context={'filename': file.filename}
        )
        raise HTTPException(status_code=500, detail=f"OCR processing error: {e}")

@router.get("/download/{filename}")
async def download_ocr_result(filename: str):
    """Download OCR-processed PDF"""
    
    # Security check - prevent directory traversal
    if '..' in filename or '/' in filename or '\\' in filename:
        raise HTTPException(status_code=400, detail="Invalid filename")
    
    # Look for file in temporary directories
    temp_dirs = [
        tempfile.gettempdir(),
        '/tmp',
        '/var/tmp'
    ]
    
    for temp_dir in temp_dirs:
        potential_path = os.path.join(temp_dir, filename)
        if os.path.exists(potential_path):
            return FileResponse(
                potential_path,
                media_type='application/pdf',
                filename=filename
            )
    
    raise HTTPException(status_code=404, detail="File not found")

@router.post("/extract-text")
async def extract_text_from_image(
    file: UploadFile = File(...),
    languages: Optional[List[str]] = None
):
    """Extract text from image using OCR"""
    
    allowed_extensions = {'.png', '.jpg', '.jpeg', '.tiff', '.bmp', '.webp'}
    file_ext = Path(file.filename or '').suffix.lower()
    
    if file_ext not in allowed_extensions:
        raise HTTPException(
            status_code=400, 
            detail=f"Image file required. Allowed: {', '.join(allowed_extensions)}"
        )
    
    trace_id = observability_service.create_trace(
        name="ocr_text_extraction",
        metadata={
            'filename': file.filename,
            'languages': languages or ['heb', 'eng']
        }
    )
    
    try:
        with tempfile.NamedTemporaryFile(suffix=file_ext, delete=False) as tmp:
            input_path = tmp.name
            content = await file.read()
            tmp.write(content)
        
        result = ocr_service.extract_text_from_image(input_path, languages)
        
        # Cleanup
        os.unlink(input_path)
        
        observability_service.create_span(
            trace_id=trace_id,
            name="text_extraction",
            metadata={
                'input_path': input_path,
                'result': result
            }
        )
        
        if not result.get('success'):
            raise HTTPException(
                status_code=500, 
                detail=f"Text extraction failed: {result.get('error')}"
            )
        
        return result
        
    except Exception as e:
        observability_service.track_error(
            trace_id=trace_id,
            error_type=type(e).__name__,
            error_message=str(e),
            context={'filename': file.filename}
        )
        raise HTTPException(status_code=500, detail=f"Text extraction error: {e}")

@router.get("/languages")
async def get_available_languages():
    """Get available Tesseract languages"""
    return {
        'available_languages': ocr_service.tesseract_languages,
        'hebrew_supported': 'heb' in ocr_service.tesseract_languages
    }

@router.get("/validate-hebrew")
async def validate_hebrew_support():
    """Validate Hebrew OCR support"""
    result = ocr_service.validate_hebrew_support()
    
    if not result.get('hebrew_available'):
        raise HTTPException(
            status_code=500, 
            detail="Hebrew language pack not available. Please install tesseract-ocr-heb package."
        )
    
    return result

@router.post("/batch-process")
async def batch_process_pdfs(
    background_tasks: BackgroundTasks,
    input_directory: str,
    output_directory: str,
    languages: Optional[List[str]] = None
):
    """Batch process all PDFs in a directory"""
    
    if not os.path.isdir(input_directory):
        raise HTTPException(status_code=400, detail="Input directory not found")
    
    trace_id = observability_service.create_trace(
        name="ocr_batch_processing",
        metadata={
            'input_directory': input_directory,
            'output_directory': output_directory,
            'languages': languages
        }
    )
    
    try:
        result = ocr_service.batch_process_documents(
            input_directory, 
            output_directory, 
            languages
        )
        
        observability_service.create_span(
            trace_id=trace_id,
            name="batch_processing",
            metadata={
                'total_processed': result['total_processed'],
                'successful': result['successful'],
                'failed': result['failed']
            }
        )
        
        return result
        
    except Exception as e:
        observability_service.track_error(
            trace_id=trace_id,
            error_type=type(e).__name__,
            error_message=str(e)
        )
        raise HTTPException(status_code=500, detail=f"Batch processing error: {e}")