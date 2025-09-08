from fastapi import APIRouter, HTTPException, Depends
from typing import List
from sqlalchemy.orm import Session
from uuid import UUID

from database import get_db
from models import Project as ProjectModel
from packages.schemas.projects import Project, ProjectCreate, ProjectUpdate
from utils.error_handling import (
    create_not_found_error, create_database_error, ErrorCategory, ErrorSeverity,
    create_http_exception
)
from utils.validation import ProjectValidator, validate_and_raise

router = APIRouter(prefix="/projects", tags=["projects"])

@router.get("/", response_model=List[Project])
async def get_projects(db: Session = Depends(get_db)):
    """Get all projects with enhanced error handling"""
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
        raise create_database_error("fetching projects")

@router.get("/{project_id}", response_model=Project)
async def get_project(project_id: UUID, db: Session = Depends(get_db)):
    """Get a specific project by ID with enhanced error handling"""
    try:
        project = db.query(ProjectModel).filter(ProjectModel.id == project_id).first()
        if not project:
            raise create_not_found_error("project")
        
        return project
    
    except HTTPException:
        raise
    except Exception as e:
        raise create_database_error("fetching project")

@router.post("/", response_model=Project)
async def create_project(project: ProjectCreate, db: Session = Depends(get_db)):
    """Create a new project with comprehensive validation"""
    try:
        # Validate project data
        project_data = project.dict()
        validate_and_raise(ProjectValidator.validate_project_data, project_data)
        
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
    
    except HTTPException:
        raise
    except Exception as e:
        raise create_database_error("creating project")

@router.put("/{project_id}", response_model=Project)
async def update_project(project_id: UUID, project: ProjectUpdate, db: Session = Depends(get_db)):
    """Update a project with comprehensive validation"""
    try:
        db_project = db.query(ProjectModel).filter(ProjectModel.id == project_id).first()
        if not db_project:
            raise create_not_found_error("project")
        
        # Validate update data (only non-None fields)
        update_data = {k: v for k, v in project.dict().items() if v is not None}
        if update_data:
            validate_and_raise(ProjectValidator.validate_project_data, update_data)
        
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
        raise create_database_error("updating project")

@router.delete("/{project_id}")
async def delete_project(project_id: UUID, db: Session = Depends(get_db)):
    """Delete a project safely with proper cascade handling and enhanced error handling"""
    try:
        from services.project_deletion_service import project_deletion_service
        
        # Use the enhanced deletion service
        result = await project_deletion_service.delete_project_safely(project_id, db)
        return result
    
    except HTTPException:
        raise
    except Exception as e:
        raise create_database_error("deleting project")

@router.get("/{project_id}/deletion-impact")
async def get_project_deletion_impact(project_id: UUID, db: Session = Depends(get_db)):
    """Get impact analysis for project deletion with enhanced error handling"""
    try:
        from services.project_deletion_service import project_deletion_service
        
        result = await project_deletion_service.validate_project_deletion(project_id, db)
        return result
    
    except HTTPException:
        raise
    except Exception as e:
        raise create_database_error("analyzing deletion impact")