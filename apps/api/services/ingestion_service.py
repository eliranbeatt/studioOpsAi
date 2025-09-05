"""Ingestion pipeline service orchestrating OCR, parsing, extraction, and validation"""

import os
import logging
import uuid
from typing import Dict, List, Any, Optional, Tuple
from pathlib import Path
import tempfile
from datetime import datetime
from uuid import UUID

from services.ocr_service import ocr_service
from services.unstructured_service import unstructured_service
from services.instructor_service import instructor_service
from services.observability_service import observability_service

logger = logging.getLogger(__name__)

class IngestionService:
    """Service orchestrating the complete document ingestion pipeline"""
    
    def __init__(self):
        self.pipeline_stages = [
            "parse",      # Document parsing and text extraction
            "classify",   # Document type classification
            "pack",       # RAG context building
            "extract",    # Structured data extraction
            "validate",   # Data validation
            "link",       # Entity linking
            "stage"       # Results staging
        ]
    
    def process_document(self, 
                       file_path: str, 
                       document_id: UUID,
                       project_id: Optional[str] = None,
                       tags: List[str] = None,
                       trace_id: Optional[str] = None) -> Dict[str, Any]:
        """Process a document through the complete ingestion pipeline"""
        
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")
        
        if trace_id is None:
            trace_id = observability_service.create_trace(
                name="ingestion_pipeline",
                metadata={
                    'document_id': str(document_id),
                    'file_path': file_path,
                    'project_id': project_id
                }
            )
        
        try:
            results = {}
            
            # Stage 1: Parse - OCR and document parsing
            parse_result = self._parse_stage(file_path, trace_id)
            results['parse'] = parse_result
            
            if not parse_result.get('success', False):
                return self._build_failure_result("parse", results, trace_id)
            
            # Stage 2: Classify - Document type classification
            classify_result = self._classify_stage(parse_result['extracted_text'], trace_id)
            results['classify'] = classify_result
            
            # Stage 3: Pack - Build RAG context
            pack_result = self._pack_stage(parse_result, classify_result, trace_id)
            results['pack'] = pack_result
            
            # Stage 4: Extract - Structured data extraction
            extract_result = self._extract_stage(
                parse_result['extracted_text'], 
                classify_result['document_type'],
                trace_id
            )
            results['extract'] = extract_result
            
            # Stage 5: Validate - Data validation
            validate_result = self._validate_stage(extract_result, trace_id)
            results['validate'] = validate_result
            
            # Stage 6: Link - Entity linking
            link_result = self._link_stage(extract_result, trace_id)
            results['link'] = link_result
            
            # Stage 7: Stage - Prepare results for commit
            stage_result = self._stage_stage(results, trace_id)
            results['stage'] = stage_result
            
            # Store results in database
            self._store_extraction_results(document_id, results, project_id, tags)
            
            observability_service.create_span(
                trace_id=trace_id,
                name="pipeline_completed",
                metadata={
                    'document_id': str(document_id),
                    'successful_stages': len([r for r in results.values() if r.get('success', False)]),
                    'total_items_extracted': len(extract_result.get('extracted_items', [])),
                    'overall_confidence': stage_result.get('overall_confidence', 0.0)
                }
            )
            
            return {
                'success': True,
                'document_id': str(document_id),
                'results': results,
                'trace_id': trace_id,
                'pipeline_status': 'completed',
                'requires_review': stage_result.get('requires_review', False)
            }
            
        except Exception as e:
            logger.error(f"Ingestion pipeline failed: {e}")
            observability_service.track_error(
                trace_id=trace_id,
                error_type="pipeline_error",
                error_message=str(e),
                context={'document_id': str(document_id), 'file_path': file_path}
            )
            return {
                'success': False,
                'error': str(e),
                'trace_id': trace_id,
                'pipeline_status': 'failed'
            }
    
    def _parse_stage(self, file_path: str, trace_id: str) -> Dict[str, Any]:
        """Stage 1: Document parsing and text extraction"""
        
        span_id = observability_service.create_span(
            trace_id=trace_id,
            name="parse_stage",
            metadata={'file_path': file_path}
        )
        
        try:
            file_ext = Path(file_path).suffix.lower()
            
            # Handle different file types
            if file_ext == '.pdf':
                # Process PDF with OCR (especially for Hebrew)
                ocr_result = ocr_service.process_pdf_with_ocr(file_path)
                
                if ocr_result['success']:
                    # Parse the OCR'd PDF
                    parse_result = unstructured_service.parse_document(
                        ocr_result['output_path'],
                        languages=['heb', 'eng']
                    )
                else:
                    # Fallback to direct parsing
                    parse_result = unstructured_service.parse_document(file_path)
            else:
                # Parse other document types directly
                parse_result = unstructured_service.parse_document(file_path)
            
            # Extract all text for downstream processing
            extracted_text = self._extract_all_text(parse_result)
            
            observability_service.end_span(span_id, {
                'success': parse_result.get('success', False),
                'elements_count': parse_result.get('elements_count', 0),
                'extracted_text_length': len(extracted_text),
                'has_hebrew': any('\u0590' <= char <= '\u05FF' for char in extracted_text)
            })
            
            return {
                'success': parse_result.get('success', False),
                'elements_count': parse_result.get('elements_count', 0),
                'extracted_text': extracted_text,
                'metadata': parse_result.get('metadata', {}),
                'file_info': parse_result.get('file_info', {})
            }
            
        except Exception as e:
            logger.error(f"Parse stage failed: {e}")
            observability_service.end_span(span_id, {'success': False, 'error': str(e)})
            return {'success': False, 'error': str(e)}
    
    def _extract_all_text(self, parse_result: Dict[str, Any]) -> str:
        """Extract all text from parsing results"""
        if not parse_result.get('success', False):
            return ""
        
        text_parts = []
        structured_data = parse_result.get('structured_data', [])
        
        for element in structured_data:
            if element.get('text'):
                text_parts.append(element['text'])
        
        return ' '.join(text_parts)
    
    def _classify_stage(self, text: str, trace_id: str) -> Dict[str, Any]:
        """Stage 2: Document type classification"""
        
        span_id = observability_service.create_span(
            trace_id=trace_id,
            name="classify_stage",
            metadata={'text_length': len(text)}
        )
        
        try:
            # Common document types in construction/architecture
            document_types = [
                "invoice", "quote", "purchase_order", "specification", 
                "contract", "blueprint", "permit", "receipt",
                "shipping_document", "warranty", "certificate"
            ]
            
            classification = instructor_service.classify_text(text, document_types)
            
            observability_service.end_span(span_id, {
                'success': classification is not None,
                'document_type': classification['category'] if classification else 'unknown',
                'confidence': classification['confidence'] if classification else 0.0
            })
            
            return {
                'success': classification is not None,
                'document_type': classification['category'] if classification else 'unknown',
                'confidence': classification['confidence'] if classification else 0.0,
                'reasoning': classification['reasoning'] if classification else ''
            }
            
        except Exception as e:
            logger.error(f"Classify stage failed: {e}")
            observability_service.end_span(span_id, {'success': False, 'error': str(e)})
            return {'success': False, 'error': str(e)}
    
    def _pack_stage(self, parse_result: Dict[str, Any], classify_result: Dict[str, Any], trace_id: str) -> Dict[str, Any]:
        """Stage 3: Build RAG context for extraction"""
        
        span_id = observability_service.create_span(
            trace_id=trace_id,
            name="pack_stage",
            metadata={
                'document_type': classify_result.get('document_type', 'unknown'),
                'elements_count': parse_result.get('elements_count', 0)
            }
        )
        
        try:
            # Build context chunks for LLM extraction
            context_chunks = self._build_context_chunks(
                parse_result.get('structured_data', []),
                classify_result.get('document_type', 'unknown')
            )
            
            observability_service.end_span(span_id, {
                'success': True,
                'chunks_count': len(context_chunks),
                'total_context_length': sum(len(chunk) for chunk in context_chunks)
            })
            
            return {
                'success': True,
                'context_chunks': context_chunks,
                'chunks_count': len(context_chunks)
            }
            
        except Exception as e:
            logger.error(f"Pack stage failed: {e}")
            observability_service.end_span(span_id, {'success': False, 'error': str(e)})
            return {'success': False, 'error': str(e)}
    
    def _build_context_chunks(self, structured_data: List[Dict[str, Any]], doc_type: str) -> List[str]:
        """Build context chunks for RAG-based extraction"""
        chunks = []
        current_chunk = ""
        
        for element in structured_data:
            element_text = element.get('text', '')
            if not element_text:
                continue
            
            # Chunk by logical sections (titles indicate new sections)
            if element.get('type') == 'Title' and current_chunk:
                chunks.append(current_chunk.strip())
                current_chunk = element_text + "\n"
            else:
                if len(current_chunk) + len(element_text) > 2000:  # Rough chunk size limit
                    chunks.append(current_chunk.strip())
                    current_chunk = element_text + "\n"
                else:
                    current_chunk += element_text + "\n"
        
        if current_chunk:
            chunks.append(current_chunk.strip())
        
        return chunks
    
    def _extract_stage(self, text: str, doc_type: str, trace_id: str) -> Dict[str, Any]:
        """Stage 4: Structured data extraction using Instructor"""
        
        span_id = observability_service.create_span(
            trace_id=trace_id,
            name="extract_stage",
            metadata={'document_type': doc_type, 'text_length': len(text)}
        )
        
        try:
            # Define extraction schema based on document type
            extraction_schema = self._get_extraction_schema(doc_type)
            
            # Use Instructor for structured extraction
            extraction_result = instructor_service.extract_structured_data(
                text=text,
                response_model=extraction_schema,
                model="gpt-4o",
                max_retries=3
            )
            
            extracted_data = extraction_result.dict() if extraction_result else {}
            
            observability_service.end_span(span_id, {
                'success': extraction_result is not None,
                'items_extracted': len(extracted_data),
                'extraction_success': bool(extraction_result)
            })
            
            return {
                'success': extraction_result is not None,
                'extracted_data': extracted_data,
                'extracted_items': self._format_extracted_items(extracted_data, doc_type),
                'raw_extraction': str(extraction_result) if extraction_result else None
            }
            
        except Exception as e:
            logger.error(f"Extract stage failed: {e}")
            observability_service.end_span(span_id, {'success': False, 'error': str(e)})
            return {'success': False, 'error': str(e)}
    
    def _get_extraction_schema(self, doc_type: str):
        """Get Pydantic schema for extraction based on document type"""
        from pydantic import BaseModel, Field
        from typing import List, Optional
        
        # Common item schema for construction materials
        class MaterialItem(BaseModel):
            description: str = Field(description="Item description or name")
            quantity: Optional[float] = Field(description="Quantity of the item")
            unit: Optional[str] = Field(description="Unit of measurement")
            unit_price: Optional[float] = Field(description="Price per unit")
            total_price: Optional[float] = Field(description="Total price for this item")
            category: Optional[str] = Field(description="Item category")
            
        if doc_type == "invoice":
            class InvoiceExtraction(BaseModel):
                vendor_name: Optional[str] = Field(description="Vendor or supplier name")
                invoice_number: Optional[str] = Field(description="Invoice number")
                invoice_date: Optional[str] = Field(description="Invoice date")
                due_date: Optional[str] = Field(description="Payment due date")
                total_amount: Optional[float] = Field(description="Total invoice amount")
                tax_amount: Optional[float] = Field(description="Tax amount")
                items: List[MaterialItem] = Field(description="List of items on the invoice")
                
            return InvoiceExtraction
            
        elif doc_type == "quote":
            class QuoteExtraction(BaseModel):
                vendor_name: Optional[str] = Field(description="Vendor or supplier name")
                quote_number: Optional[str] = Field(description="Quote number")
                quote_date: Optional[str] = Field(description="Quote date")
                valid_until: Optional[str] = Field(description="Quote validity date")
                total_amount: Optional[float] = Field(description="Total quote amount")
                items: List[MaterialItem] = Field(description="List of quoted items")
                
            return QuoteExtraction
            
        else:
            # Generic extraction for unknown document types
            class GenericExtraction(BaseModel):
                items: List[MaterialItem] = Field(description="List of items found in the document")
                total_amount: Optional[float] = Field(description="Total amount if available")
                document_date: Optional[str] = Field(description="Document date if available")
                
            return GenericExtraction
    
    def _format_extracted_items(self, extracted_data: Dict[str, Any], doc_type: str) -> List[Dict[str, Any]]:
        """Format extracted items for database storage"""
        items = []
        
        # Extract items based on document type structure
        if doc_type == "invoice" and 'items' in extracted_data:
            items_data = extracted_data['items']
        elif doc_type == "quote" and 'items' in extracted_data:
            items_data = extracted_data['items']
        elif 'items' in extracted_data:
            items_data = extracted_data['items']
        else:
            items_data = []
        
        for i, item in enumerate(items_data):
            formatted_item = {
                'id': str(uuid.uuid4()),
                'type': doc_type,
                'title': item.get('description', ''),
                'qty': item.get('quantity'),
                'unit': item.get('unit'),
                'unit_price_nis': item.get('unit_price'),
                'total_price_nis': item.get('total_price'),
                'category': item.get('category'),
                'confidence': 0.8,  # Default confidence
                'source_ref': f"item_{i}"
            }
            items.append(formatted_item)
        
        return items
    
    def _validate_stage(self, extract_result: Dict[str, Any], trace_id: str) -> Dict[str, Any]:
        """Stage 5: Data validation"""
        
        span_id = observability_service.create_span(
            trace_id=trace_id,
            name="validate_stage",
            metadata={'items_count': len(extract_result.get('extracted_items', []))}
        )
        
        try:
            items = extract_result.get('extracted_items', [])
            validation_results = []
            
            for item in items:
                validation = self._validate_item(item)
                validation_results.append({
                    'item_id': item['id'],
                    'is_valid': validation['is_valid'],
                    'issues': validation['issues'],
                    'confidence_score': validation['confidence_score']
                })
            
            valid_count = sum(1 for v in validation_results if v['is_valid'])
            total_count = len(validation_results)
            
            observability_service.end_span(span_id, {
                'success': True,
                'valid_items': valid_count,
                'total_items': total_count,
                'validation_rate': valid_count / total_count if total_count > 0 else 1.0
            })
            
            return {
                'success': True,
                'validation_results': validation_results,
                'valid_items_count': valid_count,
                'total_items_count': total_count,
                'validation_rate': valid_count / total_count if total_count > 0 else 1.0
            }
            
        except Exception as e:
            logger.error(f"Validate stage failed: {e}")
            observability_service.end_span(span_id, {'success': False, 'error': str(e)})
            return {'success': False, 'error': str(e)}
    
    def _validate_item(self, item: Dict[str, Any]) -> Dict[str, Any]:
        """Validate a single extracted item"""
        issues = []
        confidence_score = 0.8  # Base confidence
        
        # Check for required fields
        if not item.get('title') or len(item['title'].strip()) < 2:
            issues.append('missing_or_short_description')
            confidence_score -= 0.2
        
        # Validate quantity
        if item.get('qty') is not None and item['qty'] <= 0:
            issues.append('invalid_quantity')
            confidence_score -= 0.1
        
        # Validate prices
        if item.get('unit_price_nis') is not None and item['unit_price_nis'] < 0:
            issues.append('invalid_unit_price')
            confidence_score -= 0.1
        
        if item.get('total_price_nis') is not None and item['total_price_nis'] < 0:
            issues.append('invalid_total_price')
            confidence_score -= 0.1
        
        # Price consistency check
        if (item.get('qty') and item.get('unit_price_nis') and item.get('total_price_nis')):
            expected_total = item['qty'] * item['unit_price_nis']
            if abs(expected_total - item['total_price_nis']) > 0.01:
                issues.append('price_inconsistency')
                confidence_score -= 0.15
        
        return {
            'is_valid': len(issues) == 0,
            'issues': issues,
            'confidence_score': max(0.0, min(1.0, confidence_score))
        }
    
    def _link_stage(self, extract_result: Dict[str, Any], trace_id: str) -> Dict[str, Any]:
        """Stage 6: Entity linking to existing vendors and materials"""
        
        span_id = observability_service.create_span(
            trace_id=trace_id,
            name="link_stage",
            metadata={'items_count': len(extract_result.get('extracted_items', []))}
        )
        
        try:
            items = extract_result.get('extracted_items', [])
            linking_results = []
            
            for item in items:
                linking_result = self._link_item_to_entities(item)
                linking_results.append({
                    'item_id': item['id'],
                    'vendor_matches': linking_result['vendor_matches'],
                    'material_matches': linking_result['material_matches'],
                    'best_vendor_match': linking_result['best_vendor_match'],
                    'best_material_match': linking_result['best_material_match']
                })
            
            observability_service.end_span(span_id, {
                'success': True,
                'items_linked': len(linking_results),
                'vendor_matches_found': sum(1 for r in linking_results if r['vendor_matches']),
                'material_matches_found': sum(1 for r in linking_results if r['material_matches'])
            })
            
            return {
                'success': True,
                'linking_results': linking_results,
                'summary': {
                    'total_items': len(items),
                    'items_with_vendor_matches': sum(1 for r in linking_results if r['vendor_matches']),
                    'items_with_material_matches': sum(1 for r in linking_results if r['material_matches'])
                }
            }
            
        except Exception as e:
            logger.error(f"Link stage failed: {e}")
            observability_service.end_span(span_id, {'success': False, 'error': str(e)})
            return {'success': False, 'error': str(e)}
    
    def _link_item_to_entities(self, item: Dict[str, Any]) -> Dict[str, Any]:
        """Link item to existing vendors and materials using fuzzy matching"""
        # This would typically query the database for fuzzy matches
        # For now, return mock results
        return {
            'vendor_matches': [],
            'material_matches': [],
            'best_vendor_match': None,
            'best_material_match': None
        }
    
    def _stage_stage(self, pipeline_results: Dict[str, Any], trace_id: str) -> Dict[str, Any]:
        """Stage 7: Prepare results for commit and review"""
        
        span_id = observability_service.create_span(
            trace_id=trace_id,
            name="stage_stage",
            metadata={'stages_completed': len(pipeline_results)}
        )
        
        try:
            extract_result = pipeline_results.get('extract', {})
            validate_result = pipeline_results.get('validate', {})
            link_result = pipeline_results.get('link', {})
            
            items = extract_result.get('extracted_items', [])
            validation_results = validate_result.get('validation_results', [])
            
            # Calculate overall confidence
            confidence_scores = []
            requires_review = False
            
            for i, item in enumerate(items):
                if i < len(validation_results):
                    validation = validation_results[i]
                    item_confidence = validation.get('confidence_score', 0.7)
                    confidence_scores.append(item_confidence)
                    
                    if not validation.get('is_valid', False) or item_confidence < 0.7:
                        requires_review = True
                else:
                    confidence_scores.append(0.7)  # Default confidence
                    requires_review = True
            
            overall_confidence = sum(confidence_scores) / len(confidence_scores) if confidence_scores else 0.7
            
            observability_service.end_span(span_id, {
                'success': True,
                'overall_confidence': overall_confidence,
                'requires_review': requires_review,
                'total_items': len(items)
            })
            
            return {
                'success': True,
                'overall_confidence': overall_confidence,
                'requires_review': requires_review,
                'total_items_extracted': len(items),
                'valid_items_count': validate_result.get('valid_items_count', 0),
                'validation_rate': validate_result.get('validation_rate', 0.0)
            }
            
        except Exception as e:
            logger.error(f"Stage stage failed: {e}")
            observability_service.end_span(span_id, {'success': False, 'error': str(e)})
            return {'success': False, 'error': str(e)}
    
    def _store_extraction_results(self, 
                                document_id: UUID, 
                                results: Dict[str, Any],
                                project_id: Optional[str] = None,
                                tags: List[str] = None):
        """Store extraction results in database"""
        # This would typically insert into extracted_items table
        # For now, this is a placeholder - actual DB operations would be handled by the router
        pass
    
    def _build_failure_result(self, failed_stage: str, results: Dict[str, Any], trace_id: str) -> Dict[str, Any]:
        """Build result for failed pipeline"""
        return {
            'success': False,
            'failed_stage': failed_stage,
            'results': results,
            'trace_id': trace_id,
            'pipeline_status': 'failed'
        }

# Global instance
ingestion_service = IngestionService()