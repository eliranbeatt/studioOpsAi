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
        return projects
    
    except Exception as e:
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
    """Delete a project"""
    try:
        db_project = db.query(ProjectModel).filter(ProjectModel.id == project_id).first()
        if not db_project:
            raise HTTPException(status_code=404, detail="Project not found")
        
        db.delete(db_project)
        db.commit()
        
        return {"message": "Project deleted successfully"}
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error deleting project: {e}")