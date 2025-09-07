"""
Enhanced Project Deletion Service

This service provides safe project deletion with proper handling of all dependent records
and comprehensive error handling with rollback capabilities.
"""

import logging
from typing import Dict, Any, Optional
from uuid import UUID
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from fastapi import HTTPException

from models import (
    Project, ChatSession, Document, Plan, Purchase, 
    PlanItem, GeneratedDocument
)

logger = logging.getLogger(__name__)


class ProjectDeletionService:
    """Service for safely deleting projects with proper cascade handling"""
    
    def __init__(self):
        self.logger = logger
    
    async def delete_project_safely(self, project_id: UUID, db: Session) -> Dict[str, Any]:
        """
        Safely delete a project with proper handling of all dependent records
        
        Args:
            project_id: UUID of the project to delete
            db: Database session
            
        Returns:
            Dict with deletion results and statistics
            
        Raises:
            HTTPException: If deletion fails or project not found
        """
        
        # Start transaction
        try:
            # 1. Verify project exists
            project = db.query(Project).filter(Project.id == project_id).first()
            if not project:
                raise HTTPException(
                    status_code=404,
                    detail=f"Project with ID {project_id} not found"
                )
            
            project_name = project.name
            self.logger.info(f"Starting safe deletion of project: {project_name} ({project_id})")
            
            # 2. Collect statistics before deletion
            stats = await self._collect_deletion_stats(project_id, db)
            
            # 3. Handle dependent records (foreign keys will handle this automatically now)
            # But we'll log what's happening for transparency
            
            # Chat sessions will have project_id set to NULL (SET NULL constraint)
            chat_sessions_count = db.query(ChatSession).filter(
                ChatSession.project_id == project_id
            ).count()
            
            # Documents will have project_id set to NULL (SET NULL constraint)  
            documents_count = db.query(Document).filter(
                Document.project_id == project_id
            ).count()
            
            # Purchases will have project_id set to NULL (SET NULL constraint)
            purchases_count = db.query(Purchase).filter(
                Purchase.project_id == project_id
            ).count()
            
            # Plans and plan_items will be CASCADE deleted
            plans_count = db.query(Plan).filter(Plan.project_id == project_id).count()
            
            # Generated documents will have project_id set to NULL
            generated_docs_count = db.query(GeneratedDocument).filter(
                GeneratedDocument.project_id == project_id
            ).count()
            
            self.logger.info(f"Deletion impact for project {project_name}:")
            self.logger.info(f"  - Chat sessions to unlink: {chat_sessions_count}")
            self.logger.info(f"  - Documents to unlink: {documents_count}")
            self.logger.info(f"  - Purchases to unlink: {purchases_count}")
            self.logger.info(f"  - Plans to delete: {plans_count}")
            self.logger.info(f"  - Generated documents to unlink: {generated_docs_count}")
            
            # 4. Delete the project (foreign key constraints will handle dependencies)
            db.delete(project)
            db.commit()
            
            self.logger.info(f"✅ Successfully deleted project: {project_name} ({project_id})")
            
            return {
                "success": True,
                "message": f"Project '{project_name}' deleted successfully",
                "project_id": str(project_id),
                "project_name": project_name,
                "deletion_stats": {
                    "chat_sessions_unlinked": chat_sessions_count,
                    "documents_unlinked": documents_count,
                    "purchases_unlinked": purchases_count,
                    "plans_deleted": plans_count,
                    "generated_documents_unlinked": generated_docs_count
                },
                "pre_deletion_stats": stats
            }
            
        except HTTPException:
            # Re-raise HTTP exceptions (like 404)
            db.rollback()
            raise
            
        except SQLAlchemyError as e:
            db.rollback()
            error_msg = f"Database error during project deletion: {str(e)}"
            self.logger.error(error_msg)
            raise HTTPException(
                status_code=500,
                detail=f"Failed to delete project due to database error: {str(e)}"
            )
            
        except Exception as e:
            db.rollback()
            error_msg = f"Unexpected error during project deletion: {str(e)}"
            self.logger.error(error_msg)
            raise HTTPException(
                status_code=500,
                detail=f"Failed to delete project: {str(e)}"
            )
    
    async def _collect_deletion_stats(self, project_id: UUID, db: Session) -> Dict[str, Any]:
        """Collect statistics about what will be affected by deletion"""
        
        try:
            stats = {}
            
            # Count related records
            stats["chat_sessions"] = db.query(ChatSession).filter(
                ChatSession.project_id == project_id
            ).count()
            
            stats["documents"] = db.query(Document).filter(
                Document.project_id == project_id
            ).count()
            
            stats["purchases"] = db.query(Purchase).filter(
                Purchase.project_id == project_id
            ).count()
            
            stats["plans"] = db.query(Plan).filter(
                Plan.project_id == project_id
            ).count()
            
            # Count plan items (will be cascade deleted with plans)
            plan_ids = db.query(Plan.id).filter(Plan.project_id == project_id).subquery()
            stats["plan_items"] = db.query(PlanItem).filter(
                PlanItem.plan_id.in_(plan_ids)
            ).count()
            
            stats["generated_documents"] = db.query(GeneratedDocument).filter(
                GeneratedDocument.project_id == project_id
            ).count()
            
            return stats
            
        except Exception as e:
            self.logger.warning(f"Failed to collect deletion stats: {e}")
            return {"error": "Could not collect statistics"}
    
    async def validate_project_deletion(self, project_id: UUID, db: Session) -> Dict[str, Any]:
        """
        Validate if a project can be safely deleted and return impact analysis
        
        Args:
            project_id: UUID of the project to validate
            db: Database session
            
        Returns:
            Dict with validation results and impact analysis
        """
        
        try:
            # Check if project exists
            project = db.query(Project).filter(Project.id == project_id).first()
            if not project:
                return {
                    "can_delete": False,
                    "reason": "Project not found",
                    "project_exists": False
                }
            
            # Collect impact statistics
            stats = await self._collect_deletion_stats(project_id, db)
            
            # Determine if deletion is safe
            # With our new foreign key constraints, deletion should always be safe
            can_delete = True
            warnings = []
            
            # Add warnings for data that will be affected
            if stats.get("chat_sessions", 0) > 0:
                warnings.append(f"{stats['chat_sessions']} chat sessions will be unlinked from this project")
            
            if stats.get("documents", 0) > 0:
                warnings.append(f"{stats['documents']} documents will be unlinked from this project")
            
            if stats.get("purchases", 0) > 0:
                warnings.append(f"{stats['purchases']} purchase records will be unlinked from this project")
            
            if stats.get("plans", 0) > 0:
                warnings.append(f"{stats['plans']} plans and {stats.get('plan_items', 0)} plan items will be permanently deleted")
            
            return {
                "can_delete": can_delete,
                "project_exists": True,
                "project_name": project.name,
                "impact_analysis": stats,
                "warnings": warnings,
                "safe_deletion": True,
                "message": "Project can be safely deleted with the current database constraints"
            }
            
        except Exception as e:
            self.logger.error(f"Error validating project deletion: {e}")
            return {
                "can_delete": False,
                "reason": f"Validation error: {str(e)}",
                "error": True
            }


# Global instance
project_deletion_service = ProjectDeletionService()