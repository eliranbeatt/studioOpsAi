"""OCR service for Hebrew document processing with OCRmyPDF and Tesseract"""

import os
import tempfile
import logging
from pathlib import Path
from typing import Optional, Dict, Any, List
import subprocess
import shutil

logger = logging.getLogger(__name__)

class OCRService:
    """Service for OCR processing with Hebrew support"""
    
    def __init__(self):
        self.tesseract_languages = self._get_available_languages()
        
    def _get_available_languages(self) -> List[str]:
        """Get available Tesseract languages"""
        try:
            result = subprocess.run(
                ['tesseract', '--list-langs'],
                capture_output=True, text=True, check=True
            )
            languages = result.stdout.strip().split('\n')[1:]  # Skip first line
            return languages
        except (subprocess.CalledProcessError, FileNotFoundError) as e:
            logger.warning(f"Failed to get Tesseract languages: {e}")
            return ['eng']  # Default to English
    
    def process_pdf_with_ocr(self, 
                           input_pdf_path: str, 
                           output_pdf_path: Optional[str] = None,
                           languages: List[str] = None) -> Dict[str, Any]:
        """Process PDF with OCR using OCRmyPDF with Hebrew support"""
        
        if languages is None:
            languages = ['heb', 'eng']  # Hebrew + English fallback
        
        # Filter to only available languages
        available_langs = [lang for lang in languages if lang in self.tesseract_languages]
        if not available_langs:
            available_langs = ['eng']  # Fallback to English
        
        lang_param = '+'.join(available_langs)
        
        try:
            # Create temporary output path if not provided
            if output_pdf_path is None:
                output_pdf_path = self._get_temp_output_path(input_pdf_path)
            
            # Build OCRmyPDF command
            cmd = [
                'ocrmypdf',
                '--language', lang_param,
                '--output-type', 'pdf',
                '--deskew',  # Deskew crooked pages
                '--clean',  # Clean final output
                '--optimize', '1',  # Optimize PDF
                '--force-ocr',  # Force OCR even if text exists
                '--jobs', str(os.cpu_count() or 4),  # Use available CPUs
                input_pdf_path,
                output_pdf_path
            ]
            
            logger.info(f"Running OCR command: {' '.join(cmd)}")
            
            # Execute OCR process
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=True
            )
            
            # Extract text from OCR'd PDF for validation
            extracted_text = self._extract_text_from_pdf(output_pdf_path, available_langs)
            
            return {
                'success': True,
                'output_path': output_pdf_path,
                'languages_used': available_langs,
                'extracted_text_length': len(extracted_text),
                'has_hebrew_text': any('\u0590' <= char <= '\u05FF' for char in extracted_text),
                'command_output': result.stdout
            }
            
        except subprocess.CalledProcessError as e:
            logger.error(f"OCR process failed: {e.stderr}")
            return {
                'success': False,
                'error': e.stderr,
                'exit_code': e.returncode
            }
        except Exception as e:
            logger.error(f"Unexpected error during OCR: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def _get_temp_output_path(self, input_path: str) -> str:
        """Generate temporary output path"""
        input_path_obj = Path(input_path)
        temp_dir = tempfile.mkdtemp()
        return str(Path(temp_dir) / f"ocr_{input_path_obj.name}")
    
    def _extract_text_from_pdf(self, pdf_path: str, languages: List[str]) -> str:
        """Extract text from PDF using pdftotext for validation"""
        try:
            cmd = [
                'pdftotext',
                pdf_path,
                '-'  # Output to stdout
            ]
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=True
            )
            
            return result.stdout
            
        except (subprocess.CalledProcessError, FileNotFoundError):
            # Fallback to empty text if extraction fails
            return ""
    
    def extract_text_from_image(self, image_path: str, languages: List[str] = None) -> Dict[str, Any]:
        """Extract text from image using Tesseract directly"""
        
        if languages is None:
            languages = ['heb', 'eng']
        
        available_langs = [lang for lang in languages if lang in self.tesseract_languages]
        if not available_langs:
            available_langs = ['eng']
        
        lang_param = '+'.join(available_langs)
        
        try:
            cmd = [
                'tesseract',
                image_path,
                'stdout',  # Output to stdout
                '-l', lang_param,
                '--psm', '6'  # Assume uniform block of text
            ]
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=True
            )
            
            extracted_text = result.stdout.strip()
            
            return {
                'success': True,
                'extracted_text': extracted_text,
                'languages_used': available_langs,
                'text_length': len(extracted_text),
                'has_hebrew_text': any('\u0590' <= char <= '\u05FF' for char in extracted_text)
            }
            
        except subprocess.CalledProcessError as e:
            logger.error(f"Tesseract extraction failed: {e.stderr}")
            return {
                'success': False,
                'error': e.stderr,
                'exit_code': e.returncode
            }
    
    def batch_process_documents(self, 
                              input_directory: str, 
                              output_directory: str,
                              languages: List[str] = None) -> Dict[str, Any]:
        """Batch process all PDFs in a directory"""
        
        input_path = Path(input_directory)
        output_path = Path(output_directory)
        output_path.mkdir(parents=True, exist_ok=True)
        
        results = []
        pdf_files = list(input_path.glob('*.pdf'))
        
        for pdf_file in pdf_files:
            output_file = output_path / pdf_file.name
            
            result = self.process_pdf_with_ocr(
                str(pdf_file),
                str(output_file),
                languages
            )
            
            results.append({
                'input_file': str(pdf_file),
                'output_file': str(output_file),
                **result
            })
        
        return {
            'total_processed': len(results),
            'successful': len([r for r in results if r.get('success')]),
            'failed': len([r for r in results if not r.get('success')]),
            'results': results
        }
    
    def validate_hebrew_support(self) -> Dict[str, Any]:
        """Validate that Hebrew OCR support is working"""
        
        # Create a simple test image with Hebrew text
        test_text = """
        שלום עולם
        זהו טקסט בעברית לבדיקת OCR
        Hebrew OCR Test: 12345
        """
        
        try:
            # Create temporary test image
            with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp:
                test_image_path = tmp.name
            
            # Use ImageMagick to create test image (if available)
            try:
                subprocess.run([
                    'convert', 
                    '-size', '400x200', 
                    'xc:white', 
                    '-font', 'Arial',
                    '-pointsize', '16',
                    '-fill', 'black',
                    '-annotate', '+20+50', test_text.strip(),
                    test_image_path
                ], check=True, capture_output=True)
            except (subprocess.CalledProcessError, FileNotFoundError):
                # Fallback - just check if Hebrew language is available
                return {
                    'hebrew_available': 'heb' in self.tesseract_languages,
                    'available_languages': self.tesseract_languages,
                    'test_image_created': False
                }
            
            # Test Hebrew extraction
            hebrew_result = self.extract_text_from_image(test_image_path, ['heb'])
            
            # Clean up
            os.unlink(test_image_path)
            
            return {
                'hebrew_available': 'heb' in self.tesseract_languages,
                'available_languages': self.tesseract_languages,
                'test_image_created': True,
                'hebrew_extraction_success': hebrew_result.get('success', False),
                'extracted_hebrew_text': hebrew_result.get('extracted_text', '')
            }
            
        except Exception as e:
            logger.error(f"Hebrew validation failed: {e}")
            return {
                'hebrew_available': 'heb' in self.tesseract_languages,
                'available_languages': self.tesseract_languages,
                'error': str(e)
            }

# Global instance
ocr_service = OCRService()