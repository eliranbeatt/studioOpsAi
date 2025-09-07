from fastapi import APIRouter, HTTPException, Depends
from typing import List
from sqlalchemy.orm import Session
from uuid import UUID

from database import get_db
from models import Project as ProjectModel
from packages.schemas.projects import Project, ProjectCreate, ProjectUpdate

router = APIRouter(prefix="/projects", tags=["projects"])

@router.get("/", response_model=List[Project])
async def get_projects(db: Session = Depends(get_db)):
    """Get all projects"""
    try:
        projects = db.query(ProjectModel).order_by(ProjectModel.created_at.desc()).all()
        
        # Convert to dict to debug serialization issues
        result = []
        for project in projects:
            project_dict = {
                "id": str(project.id),  # Ensure UUID is converted to string
                "name": project.name,
                "client_name": project.client_name,
                "status": project.status or "draft",
                "start_date": project.start_date,
                "due_date": project.due_date,
                "budget_planned": float(project.budget_planned) if project.budget_planned else None,
                "budget_actual": float(project.budget_actual) if project.budget_actual else None,
                "board_id": project.board_id,
                "created_at": project.created_at,
                "updated_at": project.updated_at
            }
            result.append(project_dict)
        
        return result
    
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Error fetching projects: {e}")

@router.get("/{project_id}", response_model=Project)
async def get_project(project_id: UUID, db: Session = Depends(get_db)):
    """Get a specific project by ID"""
    try:
        project = db.query(ProjectModel).filter(ProjectModel.id == project_id).first()
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")
        
        return project
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching project: {e}")

@router.post("/", response_model=Project)
async def create_project(project: ProjectCreate, db: Session = Depends(get_db)):
    """Create a new project"""
    try:
        db_project = ProjectModel(
            name=project.name,
            client_name=project.client_name,
            status=project.status,
            start_date=project.start_date,
            due_date=project.due_date,
            budget_planned=project.budget_planned,
            budget_actual=project.budget_actual
        )
        
        db.add(db_project)
        db.commit()
        db.refresh(db_project)
        
        return db_project
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating project: {e}")

@router.put("/{project_id}", response_model=Project)
async def update_project(project_id: UUID, project: ProjectUpdate, db: Session = Depends(get_db)):
    """Update a project"""
    try:
        db_project = db.query(ProjectModel).filter(ProjectModel.id == project_id).first()
        if not db_project:
            raise HTTPException(status_code=404, detail="Project not found")
        
        # Update only provided fields
        if project.name is not None:
            db_project.name = project.name
        if project.client_name is not None:
            db_project.client_name = project.client_name
        if project.status is not None:
            db_project.status = project.status
        if project.start_date is not None:
            db_project.start_date = project.start_date
        if project.due_date is not None:
            db_project.due_date = project.due_date
        if project.budget_planned is not None:
            db_project.budget_planned = project.budget_planned
        if project.budget_actual is not None:
            db_project.budget_actual = project.budget_actual
        
        db.commit()
        db.refresh(db_project)
        
        return db_project
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error updating project: {e}")

@router.delete("/{project_id}")
async def delete_project(project_id: UUID, db: Session = Depends(get_db)):
    """Delete a project safely with proper cascade handling"""
    try:
        from services.project_deletion_service import project_deletion_service
        
        # Use the enhanced deletion service
        result = await project_deletion_service.delete_project_safely(project_id, db)
        return result
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error deleting project: {e}")

@router.get("/{project_id}/deletion-impact")
async def get_project_deletion_impact(project_id: UUID, db: Session = Depends(get_db)):
    """Get impact analysis for project deletion"""
    try:
        from services.project_deletion_service import project_deletion_service
        
        result = await project_deletion_service.validate_project_deletion(project_id, db)
        return result
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error analyzing deletion impact: {e}")