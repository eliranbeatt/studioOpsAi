from fastapi import APIRouter, HTTPException
from typing import List, Dict, Any, Optional
import psycopg2
import os
from uuid import UUID
import json
from datetime import datetime, timezone

from packages.schemas.projects import Document, DocumentCreate

# Optional service imports
try:
    from services.pdf_service import pdf_service
    PDF_SERVICE_AVAILABLE = True
except (ImportError, OSError) as e:
    print(f"PDF service not available: {e}")
    print("Using PDF service stub")
    from services.pdf_service_stub import pdf_service
    PDF_SERVICE_AVAILABLE = False

try:
    from services.trello_service import trello_service
    TRELLO_SERVICE_AVAILABLE = True
except ImportError as e:
    print(f"Trello service not available: {e}")
    TRELLO_SERVICE_AVAILABLE = False
    trello_service = None

router = APIRouter(prefix="/documents", tags=["documents"])

def get_db_connection():
    """Get a database connection"""
    try:
        conn = psycopg2.connect(
            os.getenv('DATABASE_URL', 'postgresql://studioops:studioops@localhost:5432/studioops')
        )
        return conn
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database connection failed: {e}")

@router.get("/project/{project_id}", response_model=List[Document])
async def get_project_documents(project_id: UUID):
    """Get all documents for a project"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, project_id, type, path, snapshot_jsonb, version, created_by, created_at
            FROM documents WHERE project_id = %s ORDER BY created_at DESC
        """, (str(project_id),))
        
        documents = []
        for row in cursor.fetchall():
            documents.append({
                "id": row[0],
                "project_id": row[1],
                "type": row[2],
                "path": row[3],
                "snapshot_jsonb": json.loads(row[4]) if row[4] else None,
                "version": row[5],
                "created_by": row[6],
                "created_at": row[7]
            })
        
        cursor.close()
        conn.close()
        return documents
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching documents: {e}")

@router.get("/{document_id}", response_model=Document)
async def get_document(document_id: UUID):
    """Get a specific document by ID"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, project_id, type, path, snapshot_jsonb, version, created_by, created_at
            FROM documents WHERE id = %s
        """, (str(document_id),))
        
        row = cursor.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Document not found")
        
        document = {
            "id": row[0],
            "project_id": row[1],
            "type": row[2],
            "path": row[3],
            "snapshot_jsonb": json.loads(row[4]) if row[4] else None,
            "version": row[5],
            "created_by": row[6],
            "created_at": row[7]
        }
        
        cursor.close()
        conn.close()
        return document
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching document: {e}")

@router.post("/", response_model=Document)
async def create_document(document: DocumentCreate):
    """Create a new document"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Check if project exists
        cursor.execute("SELECT id FROM projects WHERE id = %s", (str(document.project_id),))
        if not cursor.fetchone():
            raise HTTPException(status_code=404, detail="Project not found")
        
        # Create document
        cursor.execute("""
            INSERT INTO documents (project_id, type, path, snapshot_jsonb, version, created_by)
            VALUES (%s, %s, %s, %s, %s, 'system')
            RETURNING id, created_at
        """, (
            str(document.project_id), document.type, document.path,
            json.dumps(document.snapshot_jsonb) if document.snapshot_jsonb else None,
            document.version
        ))
        
        result = cursor.fetchone()
        conn.commit()
        
        new_document = {
            "id": result[0],
            "project_id": document.project_id,
            "type": document.type,
            "path": document.path,
            "snapshot_jsonb": document.snapshot_jsonb,
            "version": document.version,
            "created_by": "system",
            "created_at": result[1]
        }
        
        cursor.close()
        conn.close()
        return new_document
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating document: {e}")

@router.delete("/{document_id}")
async def delete_document(document_id: UUID):
    """Delete a document"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("DELETE FROM documents WHERE id = %s RETURNING id", (str(document_id),))
        
        if not cursor.fetchone():
            raise HTTPException(status_code=404, detail="Document not found")
        
        conn.commit()
        cursor.close()
        conn.close()
        
        return {"message": "Document deleted successfully"}
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error deleting document: {e}")

@router.post("/project/{project_id}/export/trello")
async def export_to_trello(project_id: UUID):
    """Export project tasks to Trello"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Get project details
        cursor.execute("""
            SELECT name, board_id FROM projects WHERE id = %s
        """, (str(project_id),))
        
        project = cursor.fetchone()
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")
        
        project_name, existing_board_id = project
        
        # Get latest approved plan
        cursor.execute("""
            SELECT id FROM plans 
            WHERE project_id = %s AND status = 'approved'
            ORDER BY version DESC LIMIT 1
        """, (str(project_id),))
        
        plan_row = cursor.fetchone()
        if not plan_row:
            raise HTTPException(status_code=404, detail="No approved plan found")
        
        plan_id = plan_row[0]
        
        # Get plan items for tasks
        cursor.execute("""
            SELECT id, category, title, description, quantity, unit, 
                   labor_hours, lead_time_days, risk_level
            FROM plan_items WHERE plan_id = %s
        """, (str(plan_id),))
        
        tasks = []
        for item in cursor.fetchall():
            tasks.append({
                'external_id': str(item[0]),
                'category': item[1],
                'title': item[2],
                'description': item[3] or '',
                'quantity': item[4],
                'unit': item[5],
                'labor_hours': item[6],
                'lead_time_days': item[7],
                'risk_level': item[8]
            })
        
        cursor.close()
        conn.close()
        
        # Ensure Trello board exists
        board_info = trello_service.ensure_board_structure(str(project_id), project_name)
        if not board_info:
            raise HTTPException(status_code=500, detail="Trello integration not configured")
        
        # Convert plan items to Trello cards
        cards_data = []
        for task in tasks:
            cards_data.append({
                'external_id': task['external_id'],
                'title': f"{task['title']} ({task['quantity']} {task['unit']})",
                'description': _create_task_description(task),
                'list_name': 'To Do',
                'labels': [task['category'], task['risk_level']] if task['risk_level'] else [task['category']],
                'due_date': _calculate_due_date(task)
            })
        
        # Export to Trello
        result = trello_service.upsert_cards(board_info['board_id'], cards_data)
        
        # Update project with board ID if not already set
        if not existing_board_id and board_info['board_id']:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE projects SET board_id = %s WHERE id = %s",
                (board_info['board_id'], str(project_id))
            )
            conn.commit()
            cursor.close()
            conn.close()
        
        return {
            'project_id': project_id,
            'project_name': project_name,
            'board_url': board_info['board_url'],
            'export_result': result,
            'tasks_exported': len(tasks)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error exporting to Trello: {e}")

def _create_task_description(self, task: Dict[str, Any]) -> str:
    """Create detailed task description for Trello card"""
    description = f"""{task['description']}

---

**פרטי המשימה:**
- **קטגוריה:** {task['category']}
- **כמות:** {task['quantity']} {task['unit']}
- **שעות עבודה משוערות:** {task['labor_hours'] or 'לא צוין'}
- **זמן אספקה:** {task['lead_time_days'] or 'לא צוין'} ימים
- **רמת סיכון:** {task['risk_level'] or 'רגילה'}

**מזהה:** {task['external_id']}
"""
    return description.strip()

def _calculate_due_date(self, task: Dict[str, Any]) -> Optional[str]:
    """Calculate due date based on lead time"""
    if task.get('lead_time_days'):
        from datetime import datetime, timedelta
        due_date = datetime.now() + timedelta(days=task['lead_time_days'])
        return due_date.isoformat()
    return None

@router.get("/{document_id}/download")
async def download_document(document_id: UUID):
    """Download a document file"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute(
            """SELECT path, snapshot_jsonb FROM documents WHERE id = %s""",
            (str(document_id),)
        )
        
        row = cursor.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Document not found")
        
        document_path = row[0]
        snapshot = json.loads(row[1]) if row[1] else None
        
        cursor.close()
        conn.close()
        
        # For quotes, generate the PDF on demand if needed
        if document_path.endswith('.pdf') and snapshot:
            if not PDF_SERVICE_AVAILABLE:
                raise HTTPException(status_code=503, detail="PDF generation not available")
            # Generate PDF file
            pdf_path = pdf_service.generate_quote_pdf(snapshot)
            
            # Return file response
            from fastapi.responses import FileResponse
            return FileResponse(
                pdf_path, 
                media_type='application/pdf',
                filename=f"quote_{snapshot.get('project_name', 'document')}.pdf"
            )
        
        raise HTTPException(status_code=404, detail="Document file not available")
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error downloading document: {e}")

@router.post("/generate/quote/{project_id}")
async def generate_quote_document(project_id: UUID):
    """Generate a quote document for a project"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Get project details
        cursor.execute("""
            SELECT name, client_name FROM projects WHERE id = %s
        """, (str(project_id),))
        
        project = cursor.fetchone()
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")
        
        # Get latest plan
        cursor.execute("""
            SELECT id FROM plans 
            WHERE project_id = %s AND status = 'approved'
            ORDER BY version DESC LIMIT 1
        """, (str(project_id),))
        
        plan_row = cursor.fetchone()
        if not plan_row:
            raise HTTPException(status_code=404, detail="No approved plan found")
        
        plan_id = plan_row[0]
        
        # Get plan items with totals
        cursor.execute("""
            SELECT category, title, description, quantity, unit, unit_price, subtotal
            FROM plan_items WHERE plan_id = %s ORDER BY category, title
        """, (str(plan_id),))
        
        items = []
        total = 0.0
        for item_row in cursor.fetchall():
            item = {
                "category": item_row[0],
                "title": item_row[1],
                "description": item_row[2],
                "quantity": float(item_row[3]),
                "unit": item_row[4],
                "unit_price": float(item_row[5]) if item_row[5] else 0,
                "subtotal": float(item_row[6]) if item_row[6] else 0
            }
            items.append(item)
            total += item["subtotal"]
        
        # Create document snapshot with actual timestamp
        snapshot = {
            "project_name": project[0],
            "client_name": project[1],
            "items": items,
            "total": total,
            "currency": "NIS",
            "generated_at": datetime.now(timezone.utc).isoformat()
        }
        
        # Generate actual PDF file
        if not PDF_SERVICE_AVAILABLE:
            raise HTTPException(status_code=503, detail="PDF generation not available")
        document_path = pdf_service.generate_quote_pdf(snapshot)
        
        # Create relative path for storage
        relative_path = f"/documents/{project_id}/quote_{int(total)}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        
        cursor.execute("""
            INSERT INTO documents (project_id, type, path, snapshot_jsonb, version, created_by)
            VALUES (%s, 'quote', %s, %s, 1, 'system')
            RETURNING id, created_at
        """, (str(project_id), relative_path, json.dumps(snapshot)))
        
        result = cursor.fetchone()
        conn.commit()
        
        # Return document info with both paths
        document = {
            "id": result[0],
            "project_id": project_id,
            "type": "quote",
            "path": relative_path,
            "absolute_path": document_path,  # Full path to generated PDF
            "snapshot_jsonb": snapshot,
            "version": 1,
            "created_by": "system",
            "created_at": result[1]
        }
        
        cursor.close()
        conn.close()
        return document
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating quote document: {e}")