"""PDF generation service with Hebrew RTL support"""

from typing import Dict, Any, List
from datetime import datetime
import os
import tempfile

# Optional WeasyPrint import
try:
    from weasyprint import HTML, CSS
    from weasyprint.text.fonts import FontConfiguration
    WEASYPRINT_AVAILABLE = True
except ImportError:
    print("WeasyPrint not available - PDF generation disabled")
    WEASYPRINT_AVAILABLE = False
    HTML = None
    CSS = None
    FontConfiguration = None
except OSError as e:
    print(f"WeasyPrint system libraries not available: {e}")
    print("PDF generation disabled")
    WEASYPRINT_AVAILABLE = False
    HTML = None
    CSS = None
    FontConfiguration = None

class PDFService:
    """Service for generating PDF documents with Hebrew support"""
    
    def __init__(self):
        self.output_dir = os.getenv('PDF_OUTPUT_DIR', '/tmp/documents')
        os.makedirs(self.output_dir, exist_ok=True)
        self.available = WEASYPRINT_AVAILABLE
    
    def generate_quote_pdf(self, quote_data: Dict[str, Any], output_path: str = None) -> str:
        """Generate a quote PDF with Hebrew RTL support"""
        
        if not self.available:
            raise RuntimeError("PDF generation not available - WeasyPrint not installed")
        
        # Prepare HTML content with RTL support
        html_content = self._generate_quote_html(quote_data)
        
        # Generate CSS with RTL support
        css = CSS(string=self._get_hebrew_css())
        
        # Generate PDF
        if output_path is None:
            output_path = os.path.join(
                self.output_dir, 
                f"quote_{quote_data.get('project_name', 'unknown')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
            )
        
        html = HTML(string=html_content)
        html.write_pdf(output_path, stylesheets=[css])
        
        return output_path
    
    def _generate_quote_html(self, data: Dict[str, Any]) -> str:
        """Generate HTML content for quote with Hebrew RTL"""
        
        items_html = ""
        for item in data.get('items', []):
            items_html += f"""
            <tr class="item-row">
                <td class="item-title" dir="rtl">{item.get('title', '')}</td>
                <td class="item-description" dir="rtl">{item.get('description', '')}</td>
                <td class="item-quantity">{item.get('quantity', 0)}</td>
                <td class="item-unit" dir="rtl">{item.get('unit', '')}</td>
                <td class="item-price">₪{item.get('unit_price', 0):.2f}</td>
                <td class="item-subtotal">₪{item.get('subtotal', 0):.2f}</td>
            </tr>
            """
        
        generated_at = data.get('generated_at', datetime.now().isoformat())
        if isinstance(generated_at, str):
            generated_at = datetime.fromisoformat(generated_at.replace('Z', '+00:00'))
        
        html = f"""
        <!DOCTYPE html>
        <html dir="rtl" lang="he">
        <head>
            <meta charset="UTF-8">
            <title>הצעת מחיר - {data.get('project_name', '')}</title>
        </head>
        <body>
            <div class="header">
                <h1>הצעת מחיר</h1>
                <div class="project-info">
                    <p><strong>פרויקט:</strong> {data.get('project_name', '')}</p>
                    <p><strong>לקוח:</strong> {data.get('client_name', '')}</p>
                    <p><strong>תאריך:</strong> {generated_at.strftime('%d/%m/%Y %H:%M')}</p>
                </div>
            </div>
            
            <div class="items-table">
                <table>
                    <thead>
                        <tr>
                            <th>פריט</th>
                            <th>תיאור</th>
                            <th>כמות</th>
                            <th>יחידה</th>
                            <th>מחיר יחידה</th>
                            <th>סה"כ</th>
                        </tr>
                    </thead>
                    <tbody>
                        {items_html}
                    </tbody>
                </table>
            </div>
            
            <div class="footer">
                <div class="total">
                    <h2>סה"כ: ₪{data.get('total', 0):.2f}</h2>
                </div>
                <div class="notes">
                    <p><strong>מטבע:</strong> {data.get('currency', 'NIS')}</p>
                    <p><strong>הערות:</strong> המחירים כוללים מע"מ לפי החוק</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        return html
    
    def _get_hebrew_css(self) -> str:
        """Get CSS for Hebrew RTL documents"""
        return """
        @page {{
            size: A4;
            margin: 2cm;
            @top-right {{
                content: "הצעת מחיר";
                font-family: 'Arial', 'Helvetica', sans-serif;
                font-size: 12pt;
            }}
        }}
        
        body {{
            font-family: 'Arial', 'Helvetica', sans-serif;
            line-height: 1.6;
            direction: rtl;
            text-align: right;
        }}
        
        .header {{
            margin-bottom: 2cm;
            border-bottom: 2px solid #333;
            padding-bottom: 1cm;
        }}
        
        .header h1 {{
            font-size: 24pt;
            color: #2c3e50;
            margin-bottom: 0.5cm;
            text-align: center;
        }}
        
        .project-info p {{
            margin: 0.2cm 0;
            font-size: 12pt;
        }}
        
        .items-table {{
            margin: 1cm 0;
        }}
        
        table {{
            width: 100%;
            border-collapse: collapse;
            margin: 1cm 0;
        }}
        
        th, td {{
            padding: 0.3cm;
            border: 1px solid #ddd;
            text-align: center;
        }}
        
        th {{
            background-color: #f8f9fa;
            font-weight: bold;
            font-size: 11pt;
        }}
        
        .item-title, .item-description {{
            text-align: right;
        }}
        
        .item-title {{
            font-weight: bold;
        }}
        
        .footer {{
            margin-top: 2cm;
            border-top: 2px solid #333;
            padding-top: 1cm;
        }}
        
        .total h2 {{
            color: #2c3e50;
            text-align: left;
            margin: 0;
        }}
        
        .notes {{
            margin-top: 0.5cm;
            font-size: 10pt;
            color: #666;
        }}
        
        .notes p {{
            margin: 0.2cm 0;
        }}
        """

# Global instance
pdf_service = PDFService()