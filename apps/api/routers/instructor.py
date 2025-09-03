"""Instructor LLM structured output API endpoints"""

from fastapi import APIRouter, HTTPException
from typing import List, Optional, Dict, Any, Type
from pydantic import BaseModel, Field
import json

from ..services.instructor_service import instructor_service
from ..services.observability_service import observability_service

router = APIRouter(prefix="/instructor", tags=["instructor"])

# Example Pydantic models for common use cases
class ExtractionResult(BaseModel):
    success: bool
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    confidence: float = 0.0

class HealthCheckResponse(BaseModel):
    enabled: bool
    openai_configured: bool
    model_availability: List[str]
    service_status: str

@router.post("/extract-structured")
async def extract_structured_data(
    text: str,
    response_model: Dict[str, Any],
    model: str = "gpt-4o",
    max_retries: int = 3
):
    """Extract structured data from text using custom Pydantic model definition"""
    
    if not instructor_service.enabled:
        raise HTTPException(status_code=500, detail="Instructor service not enabled")
    
    if not text.strip():
        raise HTTPException(status_code=400, detail="Text cannot be empty")
    
    trace_id = observability_service.create_trace(
        name="instructor_structured_extraction",
        metadata={
            'model': model,
            'max_retries': max_retries,
            'text_length': len(text),
            'response_model_keys': list(response_model.keys())
        }
    )
    
    try:
        # Dynamically create Pydantic model from request
        dynamic_model = type('DynamicModel', (BaseModel,), response_model)
        
        result = instructor_service.extract_structured_data(
            text=text,
            response_model=dynamic_model,
            model=model,
            max_retries=max_retries
        )
        
        observability_service.create_span(
            trace_id=trace_id,
            name="llm_extraction",
            metadata={
                'model_used': model,
                'extraction_success': result is not None,
                'result_fields': list(result.dict().keys()) if result else []
            }
        )
        
        if not result:
            raise HTTPException(status_code=500, detail="LLM extraction failed")
        
        return ExtractionResult(
            success=True,
            result=result.dict(),
            confidence=1.0
        )
        
    except Exception as e:
        observability_service.track_error(
            trace_id=trace_id,
            error_type=type(e).__name__,
            error_message=str(e),
            context={'text_preview': text[:100] + '...' if len(text) > 100 else text}
        )
        raise HTTPException(status_code=500, detail=f"Structured extraction error: {e}")

@router.post("/extract-with-fallback")
async def extract_with_fallback(
    text: str,
    response_model: Dict[str, Any],
    models: Optional[List[str]] = None
):
    """Extract data with model fallback strategy"""
    
    if not instructor_service.enabled:
        raise HTTPException(status_code=500, detail="Instructor service not enabled")
    
    trace_id = observability_service.create_trace(
        name="instructor_fallback_extraction",
        metadata={
            'models': models or ["gpt-4o", "gpt-4-turbo", "gpt-3.5-turbo"],
            'text_length': len(text)
        }
    )
    
    try:
        dynamic_model = type('DynamicModel', (BaseModel,), response_model)
        
        result = instructor_service.extract_with_fallback(
            text=text,
            response_model=dynamic_model,
            models=models
        )
        
        observability_service.create_span(
            trace_id=trace_id,
            name="fallback_extraction",
            metadata={
                'success': result is not None,
                'result_type': type(result).__name__ if result else None
            }
        )
        
        if not result:
            raise HTTPException(status_code=500, detail="All models failed for extraction")
        
        return ExtractionResult(
            success=True,
            result=result.dict(),
            confidence=1.0
        )
        
    except Exception as e:
        observability_service.track_error(
            trace_id=trace_id,
            error_type=type(e).__name__,
            error_message=str(e)
        )
        raise HTTPException(status_code=500, detail=f"Fallback extraction error: {e}")

@router.post("/classify-text")
async def classify_text(
    text: str,
    categories: List[str],
    model: str = "gpt-4o"
):
    """Classify text into predefined categories"""
    
    if not instructor_service.enabled:
        raise HTTPException(status_code=500, detail="Instructor service not enabled")
    
    if not categories:
        raise HTTPException(status_code=400, detail="Categories list cannot be empty")
    
    trace_id = observability_service.create_trace(
        name="instructor_text_classification",
        metadata={
            'model': model,
            'categories_count': len(categories),
            'text_length': len(text)
        }
    )
    
    try:
        result = instructor_service.classify_text(
            text=text,
            categories=categories,
            model=model
        )
        
        observability_service.create_span(
            trace_id=trace_id,
            name="text_classification",
            metadata={
                'classification_result': result,
                'selected_category': result['category'] if result else None
            }
        )
        
        if not result:
            raise HTTPException(status_code=500, detail="Text classification failed")
        
        return {
            'success': True,
            'classification': result,
            'text_preview': text[:200] + '...' if len(text) > 200 else text
        }
        
    except Exception as e:
        observability_service.track_error(
            trace_id=trace_id,
            error_type=type(e).__name__,
            error_message=str(e)
        )
        raise HTTPException(status_code=500, detail=f"Text classification error: {e}")

@router.post("/summarize-document")
async def summarize_document(
    text: str,
    model: str = "gpt-4o",
    max_length: int = 500
):
    """Generate document summary with structured output"""
    
    if not instructor_service.enabled:
        raise HTTPException(status_code=500, detail="Instructor service not enabled")
    
    trace_id = observability_service.create_trace(
        name="instructor_document_summarization",
        metadata={
            'model': model,
            'max_length': max_length,
            'text_length': len(text)
        }
    )
    
    try:
        result = instructor_service.summarize_document(
            text=text,
            model=model,
            max_length=max_length
        )
        
        observability_service.create_span(
            trace_id=trace_id,
            name="document_summarization",
            metadata={
                'summary_generated': result is not None,
                'summary_length': len(result) if result else 0
            }
        )
        
        if not result:
            raise HTTPException(status_code=500, detail="Document summarization failed")
        
        return {
            'success': True,
            'summary': result,
            'original_length': len(text),
            'summary_length': len(result),
            'compression_ratio': round(len(result) / len(text) * 100, 2) if text else 0
        }
        
    except Exception as e:
        observability_service.track_error(
            trace_id=trace_id,
            error_type=type(e).__name__,
            error_message=str(e)
        )
        raise HTTPException(status_code=500, detail=f"Document summarization error: {e}")

@router.post("/extract-entities-advanced")
async def extract_entities_advanced(
    text: str,
    entity_types: Optional[List[str]] = None,
    model: str = "gpt-4o"
):
    """Advanced entity extraction with type validation"""
    
    if not instructor_service.enabled:
        raise HTTPException(status_code=500, detail="Instructor service not enabled")
    
    trace_id = observability_service.create_trace(
        name="instructor_advanced_entity_extraction",
        metadata={
            'model': model,
            'entity_types': entity_types,
            'text_length': len(text)
        }
    )
    
    try:
        result = instructor_service.extract_entities_advanced(
            text=text,
            entity_types=entity_types,
            model=model
        )
        
        observability_service.create_span(
            trace_id=trace_id,
            name="advanced_entity_extraction",
            metadata={
                'entities_found': sum(len(entities) for entities in result.values()) if result else 0,
                'entity_types_found': list(result.keys()) if result else []
            }
        )
        
        if not result:
            raise HTTPException(status_code=500, detail="Advanced entity extraction failed")
        
        return {
            'success': True,
            'entities': result,
            'total_entities': sum(len(entities) for entities in result.values()),
            'entity_types': list(result.keys())
        }
        
    except Exception as e:
        observability_service.track_error(
            trace_id=trace_id,
            error_type=type(e).__name__,
            error_message=str(e)
        )
        raise HTTPException(status_code=500, detail=f"Advanced entity extraction error: {e}")

@router.post("/validate-extraction")
async def validate_extraction(
    text: str,
    response_model: Dict[str, Any],
    expected_fields: Optional[List[str]] = None,
    model: str = "gpt-4o"
):
    """Validate extraction results with confidence scoring"""
    
    if not instructor_service.enabled:
        raise HTTPException(status_code=500, detail="Instructor service not enabled")
    
    trace_id = observability_service.create_trace(
        name="instructor_extraction_validation",
        metadata={
            'model': model,
            'expected_fields': expected_fields,
            'text_length': len(text)
        }
    )
    
    try:
        dynamic_model = type('DynamicModel', (BaseModel,), response_model)
        
        result = instructor_service.validate_extraction(
            text=text,
            response_model=dynamic_model,
            expected_fields=expected_fields,
            model=model
        )
        
        observability_service.create_span(
            trace_id=trace_id,
            name="extraction_validation",
            metadata={
                'validation_success': result['success'],
                'confidence_score': result['confidence'],
                'fields_extracted': result['fields_extracted']
            }
        )
        
        return result
        
    except Exception as e:
        observability_service.track_error(
            trace_id=trace_id,
            error_type=type(e).__name__,
            error_message=str(e)
        )
        raise HTTPException(status_code=500, detail=f"Extraction validation error: {e}")

@router.post("/batch-extract")
async def batch_extract(
    texts: List[str],
    response_model: Dict[str, Any],
    model: str = "gpt-4o"
):
    """Batch extract structured data from multiple texts"""
    
    if not instructor_service.enabled:
        raise HTTPException(status_code=500, detail="Instructor service not enabled")
    
    if not texts:
        raise HTTPException(status_code=400, detail="Texts list cannot be empty")
    
    trace_id = observability_service.create_trace(
        name="instructor_batch_extraction",
        metadata={
            'model': model,
            'texts_count': len(texts),
            'total_characters': sum(len(text) for text in texts)
        }
    )
    
    try:
        dynamic_model = type('DynamicModel', (BaseModel,), response_model)
        
        results = instructor_service.batch_extract(
            texts=texts,
            response_model=dynamic_model,
            model=model
        )
        
        successful = [r for r in results if r is not None]
        failed = [i for i, r in enumerate(results) if r is None]
        
        observability_service.create_span(
            trace_id=trace_id,
            name="batch_extraction_complete",
            metadata={
                'total_processed': len(texts),
                'successful': len(successful),
                'failed': len(failed),
                'success_rate': round(len(successful) / len(texts) * 100, 2) if texts else 0
            }
        )
        
        return {
            'success': True,
            'total_processed': len(texts),
            'successful_count': len(successful),
            'failed_count': len(failed),
            'failed_indices': failed,
            'success_rate': round(len(successful) / len(texts) * 100, 2) if texts else 0,
            'results': [r.dict() for r in successful if r],
            'errors': [f"Text at index {i} failed extraction" for i in failed]
        }
        
    except Exception as e:
        observability_service.track_error(
            trace_id=trace_id,
            error_type=type(e).__name__,
            error_message=str(e)
        )
        raise HTTPException(status_code=500, detail=f"Batch extraction error: {e}")

@router.get("/health")
async def health_check():
    """Check Instructor service health"""
    
    health = instructor_service.health_check()
    
    return HealthCheckResponse(**health)

@router.get("/models")
async def get_available_models():
    """Get available LLM models"""
    
    models = instructor_service._check_model_availability()
    
    return {
        'available_models': models,
        'recommended_models': ["gpt-4o", "gpt-4-turbo", "gpt-3.5-turbo"],
        'default_model': "gpt-4o"
    }