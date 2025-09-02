from fastapi import APIRouter, HTTPException, Depends
from typing import List, Optional
import psycopg2
import os
from uuid import UUID
from datetime import datetime

from packages.schemas.projects import Project, ProjectCreate, ProjectUpdate
from packages.schemas.auth import UserInDB
from ..services.auth_service import get_current_user

router = APIRouter(prefix="/projects", tags=["projects"])

def get_db_connection():
    """Get a database connection"""
    try:
        conn = psycopg2.connect(
            os.getenv('DATABASE_URL', 'postgresql://studioops:studioops@localhost:5432/studioops')
        )
        return conn
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database connection failed: {e}")

@router.get("/", response_model=List[Project])
async def get_projects(current_user: UserInDB = Depends(get_current_user)):
    """Get all projects"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        # Get projects that the user has access to
        cursor.execute("""
            SELECT p.id, p.name, p.client_name, p.board_id, p.status, 
                   p.start_date, p.due_date, p.budget_planned, p.budget_actual,
                   p.created_at, p.updated_at
            FROM projects p
            LEFT JOIN project_permissions pp ON p.id = pp.project_id AND pp.user_id = %s
            WHERE p.is_public = TRUE OR pp.user_id IS NOT NULL OR p.owner_id = %s
            ORDER BY p.created_at DESC
        """, (str(current_user.id), str(current_user.id)))
        
        projects = []
        for row in cursor.fetchall():
            projects.append({
                "id": row[0],
                "name": row[1],
                "client_name": row[2],
                "board_id": row[3],
                "status": row[4],
                "start_date": row[5],
                "due_date": row[6],
                "budget_planned": row[7],
                "budget_actual": row[8],
                "created_at": row[9],
                "updated_at": row[10]
            })
        
        cursor.close()
        conn.close()
        return projects
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching projects: {e}")

@router.get("/{project_id}", response_model=Project)
async def get_project(project_id: UUID, current_user: UserInDB = Depends(get_current_user)):
    """Get a specific project by ID"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        # Check if user has access to this project
        cursor.execute(
            """SELECT p.id, p.name, p.client_name, p.board_id, p.status, 
                      p.start_date, p.due_date, p.budget_planned, p.budget_actual,
                      p.created_at, p.updated_at, p.owner_id, p.is_public,
                      pp.can_view
               FROM projects p
               LEFT JOIN project_permissions pp ON p.id = pp.project_id AND pp.user_id = %s
               WHERE p.id = %s AND (p.is_public = TRUE OR pp.user_id IS NOT NULL OR p.owner_id = %s)
            """,
            (str(current_user.id), str(project_id), str(current_user.id))
        )
        
        row = cursor.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Project not found")
        
        project = {
            "id": row[0],
            "name": row[1],
            "client_name": row[2],
            "board_id": row[3],
            "status": row[4],
            "start_date": row[5],
            "due_date": row[6],
            "budget_planned": row[7],
            "budget_actual": row[8],
            "created_at": row[9],
            "updated_at": row[10]
        }
        
        cursor.close()
        conn.close()
        return project
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching project: {e}")

@router.post("/", response_model=Project)
async def create_project(project: ProjectCreate, current_user: UserInDB = Depends(get_current_user)):
    """Create a new project"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute(
            """INSERT INTO projects (name, client_name, status, start_date, due_date, 
                                   budget_planned, budget_actual, owner_id)
               VALUES (%s, %s, %s, %s, %s, %s, %s, %s) 
               RETURNING id, board_id, created_at, updated_at""",
            (project.name, project.client_name, project.status, project.start_date, 
             project.due_date, project.budget_planned, project.budget_actual, str(current_user.id))
        )
        
        result = cursor.fetchone()
        conn.commit()
        
        new_project = {
            "id": result[0],
            "name": project.name,
            "client_name": project.client_name,
            "board_id": result[1],
            "status": project.status,
            "start_date": project.start_date,
            "due_date": project.due_date,
            "budget_planned": project.budget_planned,
            "budget_actual": project.budget_actual,
            "created_at": result[2],
            "updated_at": result[3]
        }
        
        cursor.close()
        conn.close()
        return new_project
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating project: {e}")

@router.put("/{project_id}", response_model=Project)
async def update_project(project_id: UUID, project: ProjectUpdate, current_user: UserInDB = Depends(get_current_user)):
    """Update a project"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Build dynamic update query
        update_fields = []
        update_values = []
        
        if project.name is not None:
            update_fields.append("name = %s")
            update_values.append(project.name)
        if project.client_name is not None:
            update_fields.append("client_name = %s")
            update_values.append(project.client_name)
        if project.status is not None:
            update_fields.append("status = %s")
            update_values.append(project.status)
        if project.start_date is not None:
            update_fields.append("start_date = %s")
            update_values.append(project.start_date)
        if project.due_date is not None:
            update_fields.append("due_date = %s")
            update_values.append(project.due_date)
        if project.budget_planned is not None:
            update_fields.append("budget_planned = %s")
            update_values.append(project.budget_planned)
        if project.budget_actual is not None:
            update_fields.append("budget_actual = %s")
            update_values.append(project.budget_actual)
        
        if not update_fields:
            raise HTTPException(status_code=400, detail="No fields to update")
        
        # Check if user has permission to update this project
        cursor.execute(
            """SELECT p.owner_id, pp.can_edit 
               FROM projects p
               LEFT JOIN project_permissions pp ON p.id = pp.project_id AND pp.user_id = %s
               WHERE p.id = %s AND (p.owner_id = %s OR pp.can_edit = TRUE)
            """,
            (str(current_user.id), str(project_id), str(current_user.id))
        )
        
        permission = cursor.fetchone()
        if not permission:
            raise HTTPException(status_code=403, detail="No permission to update this project")
        
        update_values.append(str(project_id))
        
        query = f"""UPDATE projects SET {', '.join(update_fields)}, updated_at = NOW()
                   WHERE id = %s RETURNING board_id, created_at, updated_at"""
        
        cursor.execute(query, update_values)
        result = cursor.fetchone()
        
        if not result:
            raise HTTPException(status_code=404, detail="Project not found")
        
        conn.commit()
        
        # Get the updated project
        cursor.execute(
            """SELECT name, client_name, status, start_date, due_date, 
                      budget_planned, budget_actual
               FROM projects WHERE id = %s""",
            (str(project_id),)
        )
        
        project_data = cursor.fetchone()
        
        updated_project = {
            "id": project_id,
            "name": project_data[0],
            "client_name": project_data[1],
            "board_id": result[0],
            "status": project_data[2],
            "start_date": project_data[3],
            "due_date": project_data[4],
            "budget_planned": project_data[5],
            "budget_actual": project_data[6],
            "created_at": result[1],
            "updated_at": result[2]
        }
        
        cursor.close()
        conn.close()
        return updated_project
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error updating project: {e}")

@router.delete("/{project_id}")
async def delete_project(project_id: UUID, current_user: UserInDB = Depends(get_current_user)):
    """Delete a project"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Check if user has permission to delete this project
        cursor.execute(
            """SELECT p.owner_id, pp.can_delete 
               FROM projects p
               LEFT JOIN project_permissions pp ON p.id = pp.project_id AND pp.user_id = %s
               WHERE p.id = %s AND (p.owner_id = %s OR pp.can_delete = TRUE)
            """,
            (str(current_user.id), str(project_id), str(current_user.id))
        )
        
        permission = cursor.fetchone()
        if not permission:
            raise HTTPException(status_code=403, detail="No permission to delete this project")
        
        cursor.execute("DELETE FROM projects WHERE id = %s RETURNING id", (str(project_id),))
        
        if not cursor.fetchone():
            raise HTTPException(status_code=404, detail="Project not found")
        
        conn.commit()
        cursor.close()
        conn.close()
        
        return {"message": "Project deleted successfully"}
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error deleting project: {e}")