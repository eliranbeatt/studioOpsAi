"""Simple PDF generation service using pypdf with Hebrew RTL support"""

from typing import Dict, Any, List
from datetime import datetime
import os
from io import BytesIO
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Table, TableStyle, Spacer
from reportlab.lib import colors
from reportlab.lib.enums import TA_RIGHT, TA_CENTER
import tempfile

class SimplePDFService:
    """Simple PDF service using ReportLab for Hebrew RTL support"""
    
    def __init__(self):
        self.output_dir = os.getenv('PDF_OUTPUT_DIR', os.path.join(tempfile.gettempdir(), 'documents'))
        os.makedirs(self.output_dir, exist_ok=True)
        
        # Use Helvetica as default font - it's built into ReportLab
        self.font_name = 'Helvetica'
    
    def generate_quote_pdf(self, quote_data: Dict[str, Any], output_path: str = None) -> str:
        """Generate a quote PDF with Hebrew RTL support using ReportLab"""
        
        if output_path is None:
            output_path = os.path.join(
                self.output_dir, 
                f"quote_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
            )
        
        # Create PDF document
        doc = SimpleDocTemplate(output_path, pagesize=A4)
        story = []
        
        # Define RTL styles
        styles = getSampleStyleSheet()
        rtl_style = ParagraphStyle(
            'RTL',
            parent=styles['Normal'],
            alignment=TA_RIGHT,
            fontName=self.font_name,
            fontSize=10
        )
        
        center_style = ParagraphStyle(
            'Center',
            parent=styles['Normal'],
            alignment=TA_CENTER,
            fontName=self.font_name,
            fontSize=14,
            spaceAfter=20
        )
        
        # Header
        story.append(Paragraph("הצעת מחיר", center_style))
        
        # Project info
        project_info = [
            [Paragraph(f"<b>פרויקט:</b> {quote_data.get('project_name', '')}", rtl_style)],
            [Paragraph(f"<b>לקוח:</b> {quote_data.get('client_name', '')}", rtl_style)],
            [Paragraph(f"<b>תאריך:</b> {datetime.now().strftime('%d/%m/%Y %H:%M')}", rtl_style)]
        ]
        
        project_table = Table(project_info, colWidths=[15*cm])
        project_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'RIGHT'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('FONTNAME', (0, 0), (-1, -1), self.font_name),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ]))
        
        story.append(project_table)
        story.append(Spacer(1, 20))
        
        # Items table
        items = quote_data.get('items', [])
        if items:
            # Table headers
            table_data = [[
                Paragraph("פריט", rtl_style),
                Paragraph("תיאור", rtl_style),
                Paragraph("כמות", rtl_style),
                Paragraph("יחידה", rtl_style),
                Paragraph("מחיר יחידה", rtl_style),
                Paragraph("סה\"כ", rtl_style)
            ]]
            
            # Add items
            for item in items:
                table_data.append([
                    Paragraph(str(item.get('title', '')), rtl_style),
                    Paragraph(str(item.get('description', '')), rtl_style),
                    str(item.get('quantity', 0)),
                    Paragraph(str(item.get('unit', '')), rtl_style),
                    f"₪{item.get('unit_price', 0):.2f}",
                    f"₪{item.get('subtotal', 0):.2f}"
                ])
            
            items_table = Table(table_data, colWidths=[3*cm, 5*cm, 2*cm, 2*cm, 3*cm, 3*cm])
            items_table.setStyle(TableStyle([
                ('ALIGN', (0, 0), (-1, -1), 'RIGHT'),
                ('ALIGN', (2, 1), (2, -1), 'CENTER'),  # Quantity center
                ('ALIGN', (4, 1), (5, -1), 'RIGHT'),   # Prices right
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('FONTNAME', (0, 0), (-1, -1), self.font_name),
                ('FONTSIZE', (0, 0), (-1, -1), 9),
                ('GRID', (0, 0), (-1, -1), 1, colors.grey),
                ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 6),
                ('TOPPADDING', (0, 0), (-1, 0), 6),
            ]))
            
            story.append(items_table)
            story.append(Spacer(1, 20))
        
        # Total
        total = quote_data.get('total', 0)
        total_text = f"<b>סה\"כ: ₪{total:.2f}</b>"
        story.append(Paragraph(total_text, rtl_style))
        
        # Notes
        story.append(Spacer(1, 20))
        notes = [
            Paragraph("<b>הערות:</b>", rtl_style),
            Paragraph("המחירים כוללים מע\"מ לפי החוק", rtl_style),
            Paragraph(f"<b>מטבע:</b> {quote_data.get('currency', 'NIS')}", rtl_style)
        ]
        
        for note in notes:
            story.append(note)
        
        # Build PDF
        doc.build(story)
        
        return output_path

# Global instance
simple_pdf_service = SimplePDFService()

# Test function
def test_pdf_generation():
    """Test PDF generation"""
    test_data = {
        'project_name': 'פרויקט מבחן',
        'client_name': 'לקוח מבחן',
        'items': [
            {
                'title': 'עץ 2x4',
                'description': 'עץ אורן באיכות גבוהה',
                'quantity': 20.0,
                'unit': 'יחידה',
                'unit_price': 15.99,
                'subtotal': 319.80
            },
            {
                'title': 'ברגים',
                'description': 'ברגים פיליפס 5x50',
                'quantity': 100.0,
                'unit': 'יחידה',
                'unit_price': 0.25,
                'subtotal': 25.00
            }
        ],
        'total': 344.80,
        'currency': 'NIS'
    }
    
    service = SimplePDFService()
    pdf_path = service.generate_quote_pdf(test_data)
    print("PDF generated successfully")
    return pdf_path

if __name__ == "__main__":
    test_pdf_generation()