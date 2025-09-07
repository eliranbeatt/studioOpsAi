"""Stub PDF service when WeasyPrint is not available"""

from typing import Dict, Any
import os

class PDFServiceStub:
    """Stub PDF service that raises errors when PDF generation is attempted"""
    
    def __init__(self):
        self.available = False
        self.output_dir = os.getenv('PDF_OUTPUT_DIR', '/tmp/documents')
        os.makedirs(self.output_dir, exist_ok=True)
    
    def generate_quote_pdf(self, quote_data: Dict[str, Any], output_path: str = None) -> str:
        """Stub method that raises an error"""
        raise RuntimeError("PDF generation not available - WeasyPrint not installed")
    
    def generate_project_pdf(self, project_data: Dict[str, Any], output_path: str = None) -> str:
        """Stub method that raises an error"""
        raise RuntimeError("PDF generation not available - WeasyPrint not installed")

# Create stub instance
pdf_service = PDFServiceStub()