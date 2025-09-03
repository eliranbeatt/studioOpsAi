"""Document parsing service with Unstructured.io for intelligent document processing"""

import os
import logging
from typing import Dict, List, Any, Optional
from pathlib import Path
import tempfile
import json

from unstructured.partition.auto import partition
from unstructured.staging.base import dict_to_elements, convert_to_dict
from unstructured.documents.elements import Element, CompositeElement, Title
from unstructured.chunking.title import chunk_by_title

logger = logging.getLogger(__name__)

class UnstructuredService:
    """Service for intelligent document parsing with Unstructured.io"""
    
    def __init__(self):
        self.supported_extensions = {
            '.pdf', '.docx', '.pptx', '.xlsx', '.html', '.htm', 
            '.txt', '.eml', '.msg', '.rtf', '.epub', '.xml',
            '.png', '.jpg', '.jpeg', '.tiff', '.bmp'
        }
    
    def parse_document(self, 
                      file_path: str, 
                      strategy: str = "auto",
                      languages: List[str] = None,
                      chunking_strategy: str = "by_title") -> Dict[str, Any]:
        """Parse document using Unstructured.io with intelligent chunking"""
        
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")
        
        file_ext = Path(file_path).suffix.lower()
        if file_ext not in self.supported_extensions:
            raise ValueError(f"Unsupported file extension: {file_ext}")
        
        try:
            # Parse document with Unstructured
            elements = partition(
                filename=file_path,
                strategy=strategy,
                languages=languages or ["heb", "eng"],
                include_page_breaks=True,
                infer_table_structure=True
            )
            
            # Apply chunking strategy
            if chunking_strategy == "by_title":
                chunks = chunk_by_title(elements)
            else:
                chunks = elements
            
            # Convert to structured data
            structured_data = self._structure_elements(chunks)
            
            # Extract metadata and statistics
            metadata = self._extract_metadata(elements, file_path)
            
            return {
                'success': True,
                'elements_count': len(elements),
                'chunks_count': len(chunks),
                'structured_data': structured_data,
                'metadata': metadata,
                'file_info': {
                    'path': file_path,
                    'extension': file_ext,
                    'size': os.path.getsize(file_path)
                }
            }
            
        except Exception as e:
            logger.error(f"Document parsing failed: {e}")
            return {
                'success': False,
                'error': str(e),
                'file_path': file_path
            }
    
    def _structure_elements(self, elements: List[Element]) -> List[Dict[str, Any]]:
        """Convert Unstructured elements to structured data"""
        structured = []
        
        for i, element in enumerate(elements):
            element_data = {
                'id': f"elem_{i}",
                'type': type(element).__name__,
                'text': element.text,
                'metadata': element.metadata.to_dict() if hasattr(element, 'metadata') else {}
            }
            
            # Add specific metadata based on element type
            if isinstance(element, Title):
                element_data['heading_level'] = getattr(element.metadata, 'heading_level', 1)
            elif hasattr(element, 'category'):
                element_data['category'] = element.category
            
            structured.append(element_data)
        
        return structured
    
    def _extract_metadata(self, elements: List[Element], file_path: str) -> Dict[str, Any]:
        """Extract comprehensive metadata from parsed document"""
        
        metadata = {
            'file_name': Path(file_path).name,
            'file_size': os.path.getsize(file_path),
            'element_types': {},
            'languages_detected': set(),
            'has_tables': False,
            'has_images': False,
            'page_count': 0,
            'text_statistics': {
                'total_characters': 0,
                'total_words': 0,
                'hebrew_characters': 0,
                'english_characters': 0
            }
        }
        
        for element in elements:
            # Count element types
            elem_type = type(element).__name__
            metadata['element_types'][elem_type] = metadata['element_types'].get(elem_type, 0) + 1
            
            # Extract text statistics
            if hasattr(element, 'text') and element.text:
                text = element.text
                metadata['text_statistics']['total_characters'] += len(text)
                metadata['text_statistics']['total_words'] += len(text.split())
                
                # Detect Hebrew and English characters
                hebrew_chars = sum(1 for char in text if '\u0590' <= char <= '\u05FF')
                english_chars = sum(1 for char in text if 'a' <= char.lower() <= 'z')
                
                metadata['text_statistics']['hebrew_characters'] += hebrew_chars
                metadata['text_statistics']['english_characters'] += english_chars
                
                if hebrew_chars > 0:
                    metadata['languages_detected'].add('hebrew')
                if english_chars > 0:
                    metadata['languages_detected'].add('english')
            
            # Check for tables and images
            if hasattr(element, 'category'):
                if element.category == 'Table':
                    metadata['has_tables'] = True
                elif element.category == 'Image':
                    metadata['has_images'] = True
            
            # Extract page count from metadata
            if hasattr(element, 'metadata') and hasattr(element.metadata, 'page_number'):
                metadata['page_count'] = max(metadata['page_count'], element.metadata.page_number or 0)
        
        # Convert set to list for JSON serialization
        metadata['languages_detected'] = list(metadata['languages_detected'])
        
        return metadata
    
    def parse_from_bytes(self, 
                        file_bytes: bytes, 
                        file_extension: str,
                        **kwargs) -> Dict[str, Any]:
        """Parse document from bytes in memory"""
        
        with tempfile.NamedTemporaryFile(suffix=file_extension, delete=False) as tmp:
            tmp.write(file_bytes)
            tmp_path = tmp.name
        
        try:
            result = self.parse_document(tmp_path, **kwargs)
            os.unlink(tmp_path)
            return result
        except Exception as e:
            os.unlink(tmp_path)
            raise e
    
    def extract_tables(self, file_path: str) -> List[Dict[str, Any]]:
        """Extract tables from document with enhanced table recognition"""
        
        try:
            elements = partition(
                filename=file_path,
                strategy="hi_res",
                infer_table_structure=True,
                include_page_breaks=True
            )
            
            tables = []
            for i, element in enumerate(elements):
                if hasattr(element, 'category') and element.category == 'Table':
                    table_data = {
                        'id': f"table_{i}",
                        'text': element.text,
                        'metadata': element.metadata.to_dict() if hasattr(element, 'metadata') else {},
                        'html': getattr(element, 'html', ''),
                        'page_number': getattr(element.metadata, 'page_number', None) if hasattr(element, 'metadata') else None
                    }
                    tables.append(table_data)
            
            return tables
            
        except Exception as e:
            logger.error(f"Table extraction failed: {e}")
            return []
    
    def extract_entities(self, 
                       file_path: str, 
                       entity_types: List[str] = None) -> Dict[str, List[str]]:
        """Extract common entities from document text"""
        
        if entity_types is None:
            entity_types = ['dates', 'prices', 'emails', 'urls', 'phone_numbers']
        
        try:
            result = self.parse_document(file_path)
            if not result['success']:
                return {}
            
            all_text = ' '.join([elem['text'] for elem in result['structured_data'] if elem.get('text')])
            
            entities = {}
            
            # Simple entity extraction patterns
            if 'dates' in entity_types:
                entities['dates'] = self._extract_dates(all_text)
            
            if 'prices' in entity_types:
                entities['prices'] = self._extract_prices(all_text)
            
            if 'emails' in entity_types:
                entities['emails'] = self._extract_emails(all_text)
            
            if 'urls' in entity_types:
                entities['urls'] = self._extract_urls(all_text)
            
            if 'phone_numbers' in entity_types:
                entities['phone_numbers'] = self._extract_phone_numbers(all_text)
            
            return entities
            
        except Exception as e:
            logger.error(f"Entity extraction failed: {e}")
            return {}
    
    def _extract_dates(self, text: str) -> List[str]:
        """Extract date patterns"""
        import re
        # Simple date patterns
        patterns = [
            r'\d{1,2}/\d{1,2}/\d{4}',  # MM/DD/YYYY
            r'\d{4}-\d{1,2}-\d{1,2}',  # YYYY-MM-DD
            r'\d{1,2}\.\d{1,2}\.\d{4}',  # DD.MM.YYYY
        ]
        dates = []
        for pattern in patterns:
            dates.extend(re.findall(pattern, text))
        return list(set(dates))
    
    def _extract_prices(self, text: str) -> List[str]:
        """Extract price patterns"""
        import re
        # Price patterns with currency symbols
        patterns = [
            r'\$\s?\d+(?:\.\d{2})?',  # USD
            r'€\s?\d+(?:\.\d{2})?',   # Euro
            r'₪\s?\d+(?:\.\d{2})?',   # Shekel
            r'\d+(?:\.\d{2})?\s?(?:ש"ח|דולר|אירו)',  # Hebrew currency names
        ]
        prices = []
        for pattern in patterns:
            prices.extend(re.findall(pattern, text))
        return list(set(prices))
    
    def _extract_emails(self, text: str) -> List[str]:
        """Extract email addresses"""
        import re
        pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
        return list(set(re.findall(pattern, text)))
    
    def _extract_urls(self, text: str) -> List[str]:
        """Extract URLs"""
        import re
        pattern = r'https?://[^\s<>"{}|\\^`\[\]]+'
        return list(set(re.findall(pattern, text)))
    
    def _extract_phone_numbers(self, text: str) -> List[str]:
        """Extract phone numbers"""
        import re
        # Israeli phone number patterns
        patterns = [
            r'05\d-\d{7}',  # 05X-XXXXXXX
            r'05\d\d{7}',   # 05XXXXXXXX
            r'\+972\s?5\d-\d{7}',  # +972 5X-XXXXXXX
            r'\(05\d\)\s?\d{7}',  # (05X) XXXXXXX
        ]
        phones = []
        for pattern in patterns:
            phones.extend(re.findall(pattern, text))
        return list(set(phones))
    
    def validate_document_structure(self, file_path: str) -> Dict[str, Any]:
        """Validate document structure and extract key sections"""
        
        result = self.parse_document(file_path)
        if not result['success']:
            return result
        
        # Analyze document structure
        structured_data = result['structured_data']
        
        # Identify key sections based on title elements
        sections = []
        current_section = None
        
        for element in structured_data:
            if element['type'] == 'Title':
                if current_section:
                    sections.append(current_section)
                current_section = {
                    'title': element['text'],
                    'heading_level': element.get('heading_level', 1),
                    'content': [],
                    'element_count': 0
                }
            elif current_section:
                current_section['content'].append(element['text'])
                current_section['element_count'] += 1
        
        if current_section:
            sections.append(current_section)
        
        # Add section analysis to result
        result['document_structure'] = {
            'total_sections': len(sections),
            'sections': sections,
            'has_structured_content': len(sections) > 0
        }
        
        return result

# Global instance
unstructured_service = UnstructuredService()