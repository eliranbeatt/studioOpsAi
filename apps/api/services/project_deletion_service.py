"""
Project Deletion Service

Provides safe project deletion with proper cascade handling and transaction management.
This service ensures that all dependent records are handled appropriately when deleting projects.
"""

from sqlalchemy.orm import Session
from sqlalchemy import text, update, delete
from uuid import UUID
from typing import Dict, List, Optional
from fastapi import HTTPException
import logging

from models import (
    Project, Plan, PlanItem, ChatSession, Document, Purchase, 
    ExtractedItem, DocChunk, GeneratedDocument
)

logger = logging.getLogger(__name__)

class ProjectDeletionService:
    """Service for safely deleting projects with proper cascade handling"""
    
    async def validate_project_deletion(self, project_id: UUID, db: Session) -> Dict:
        """
        Validate if a project can be safely deleted and provide impact analysis
        
        Args:
            project_id: UUID of the project to validate
            db: Database session
            
        Returns:
            Dict with validation results and impact analysis
        """
        try:
            # Ensure we start with a clean transaction state
            db.rollback()
            # Check if project exists using raw SQL
            project_result = db.execute(
                text("SELECT id, name FROM projects WHERE id = :project_id"),
                {"project_id": str(project_id)}
            ).fetchone()
            
            if not project_result:
                return {
                    "can_delete": False,
                    "error": "Project not found",
                    "project_name": None
                }
            
            project_name = project_result[1]
            
            # Count dependent records using raw SQL to handle schema mismatches
            project_id_str = str(project_id)
            
            chat_sessions_count = db.execute(
                text("SELECT COUNT(*) FROM chat_sessions WHERE project_id = :project_id"),
                {"project_id": project_id_str}
            ).scalar()
            
            documents_count = db.execute(
                text("SELECT COUNT(*) FROM documents WHERE project_id = :project_id"),
                {"project_id": project_id_str}
            ).scalar()
            
            purchases_count = db.execute(
                text("SELECT COUNT(*) FROM purchases WHERE project_id = :project_id"),
                {"project_id": project_id_str}
            ).scalar()
            
            plans_count = db.execute(
                text("SELECT COUNT(*) FROM plans WHERE project_id = :project_id"),
                {"project_id": project_id_str}
            ).scalar()
            
            # Count plan items (will be cascade deleted with plans)
            plan_items_count = 0
            if plans_count > 0:
                plan_items_count = db.execute(
                    text("""
                        SELECT COUNT(*) FROM plan_items 
                        WHERE plan_id IN (
                            SELECT id FROM plans WHERE project_id = :project_id
                        )
                    """),
                    {"project_id": project_id_str}
                ).scalar()
            
            # Check for extracted items
            extracted_items_count = 0
            try:
                extracted_items_count = db.execute(
                    text("SELECT COUNT(*) FROM extracted_items WHERE project_id = :project_id"),
                    {"project_id": project_id_str}
                ).scalar()
            except Exception:
                # Table might not exist in all environments
                pass
            
            # Check for generated documents
            generated_docs_count = 0
            try:
                generated_docs_count = db.execute(
                    text("SELECT COUNT(*) FROM generated_documents WHERE project_id = :project_id"),
                    {"project_id": project_id_str}
                ).scalar()
            except Exception:
                # Table might not exist in all environments
                pass
            
            warnings = []
            
            # Add warnings for data that will be affected
            if chat_sessions_count > 0:
                warnings.append(f"{chat_sessions_count} chat sessions will be unlinked from this project")
            
            if documents_count > 0:
                warnings.append(f"{documents_count} documents will be unlinked from this project")
            
            if purchases_count > 0:
                warnings.append(f"{purchases_count} purchases will be unlinked from this project")
            
            if plans_count > 0:
                warnings.append(f"{plans_count} plans and {plan_items_count} plan items will be permanently deleted")
            
            if extracted_items_count > 0:
                warnings.append(f"{extracted_items_count} extracted items will be unlinked from this project")
            
            if generated_docs_count > 0:
                warnings.append(f"{generated_docs_count} generated documents will be unlinked from this project")
            
            return {
                "can_delete": True,
                "project_name": project_name,
                "safe_deletion": True,
                "impact_summary": {
                    "chat_sessions": chat_sessions_count,
                    "documents": documents_count,
                    "purchases": purchases_count,
                    "plans": plans_count,
                    "plan_items": plan_items_count,
                    "extracted_items": extracted_items_count,
                    "generated_documents": generated_docs_count
                },
                "warnings": warnings
            }
            
        except Exception as e:
            # Rollback any failed transaction
            db.rollback()
            logger.error(f"Error validating project deletion for {project_id}: {e}")
            return {
                "can_delete": False,
                "error": f"Validation failed: {str(e)}",
                "project_name": None
            }
    
    async def delete_project_safely(self, project_id: UUID, db: Session) -> Dict:
        """
        Safely delete a project with proper cascade handling
        
        Args:
            project_id: UUID of the project to delete
            db: Database session
            
        Returns:
            Dict with deletion results and statistics
        """
        try:
            # First validate the deletion
            validation = await self.validate_project_deletion(project_id, db)
            if not validation["can_delete"]:
                raise HTTPException(
                    status_code=400 if "not found" in validation.get("error", "").lower() else 500,
                    detail=validation.get("error", "Cannot delete project")
                )
            
            project_name = validation["project_name"]
            
            # Start deletion process
            logger.info(f"Starting deletion of project {project_id} ({project_name})")
            
            # Ensure we start with a clean transaction state
            db.rollback()
            
            # Convert UUID to string for database operations
            project_id_str = str(project_id)
            
            try:
                # Track deletion statistics
                deletion_stats = {
                    "chat_sessions_unlinked": 0,
                    "documents_unlinked": 0,
                    "purchases_unlinked": 0,
                    "extracted_items_unlinked": 0,
                    "generated_docs_unlinked": 0,
                    "doc_chunks_unlinked": 0,
                    "plans_deleted": 0,
                    "plan_items_deleted": 0
                }
                
                # 1. Update chat_sessions to remove project reference (SET NULL)
                logger.debug(f"Unlinking chat sessions from project {project_id}")
                chat_sessions_result = db.execute(
                    text("UPDATE chat_sessions SET project_id = NULL WHERE project_id = :project_id"),
                    {"project_id": project_id_str}
                )
                deletion_stats["chat_sessions_unlinked"] = chat_sessions_result.rowcount
                logger.debug(f"Unlinked {chat_sessions_result.rowcount} chat sessions")
                
                # 2. Update documents to remove project reference (SET NULL)
                logger.debug(f"Unlinking documents from project {project_id}")
                documents_result = db.execute(
                    text("UPDATE documents SET project_id = NULL WHERE project_id = :project_id"),
                    {"project_id": project_id_str}
                )
                deletion_stats["documents_unlinked"] = documents_result.rowcount
                logger.debug(f"Unlinked {documents_result.rowcount} documents")
                
                # 3. Update purchases to remove project reference (SET NULL)
                purchases_result = db.execute(
                    text("UPDATE purchases SET project_id = NULL WHERE project_id = :project_id"),
                    {"project_id": project_id_str}
                )
                deletion_stats["purchases_unlinked"] = purchases_result.rowcount
                
                # 4. Handle extracted_items if table exists
                try:
                    extracted_items_result = db.execute(
                        text("UPDATE extracted_items SET project_id = NULL WHERE project_id = :project_id"),
                        {"project_id": project_id_str}
                    )
                    deletion_stats["extracted_items_unlinked"] = extracted_items_result.rowcount
                except Exception as e:
                    logger.debug(f"ExtractedItem table not available: {e}")
                
                # 5. Handle generated_documents if table exists
                try:
                    generated_docs_result = db.execute(
                        text("UPDATE generated_documents SET project_id = NULL WHERE project_id = :project_id"),
                        {"project_id": project_id_str}
                    )
                    deletion_stats["generated_docs_unlinked"] = generated_docs_result.rowcount
                except Exception as e:
                    logger.debug(f"GeneratedDocument table not available: {e}")
                
                # 6. Handle doc_chunks if they reference projects (check if column exists first)
                try:
                    # Check if project_id column exists in doc_chunks
                    column_check = db.execute(
                        text("""
                            SELECT column_name FROM information_schema.columns 
                            WHERE table_name = 'doc_chunks' AND column_name = 'project_id'
                        """)
                    ).fetchone()
                    
                    if column_check:
                        doc_chunks_result = db.execute(
                            text("UPDATE doc_chunks SET project_id = NULL WHERE project_id = :project_id"),
                            {"project_id": project_id_str}
                        )
                        deletion_stats["doc_chunks_unlinked"] = doc_chunks_result.rowcount
                except Exception as e:
                    logger.debug(f"DocChunk project_id column not available: {e}")
                
                # 7. Count plan items before deletion (for statistics)
                plan_items_count = 0
                try:
                    plan_items_count = db.execute(
                        text("""
                            SELECT COUNT(*) FROM plan_items 
                            WHERE plan_id IN (
                                SELECT id FROM plans WHERE project_id = :project_id
                            )
                        """),
                        {"project_id": project_id_str}
                    ).scalar()
                    deletion_stats["plan_items_deleted"] = plan_items_count
                except Exception as e:
                    logger.debug(f"Error counting plan items: {e}")
                
                # 8. Delete plans (CASCADE will handle plan_items automatically)
                logger.debug(f"Deleting plans for project {project_id}")
                plans_result = db.execute(
                    text("DELETE FROM plans WHERE project_id = :project_id"),
                    {"project_id": project_id_str}
                )
                deletion_stats["plans_deleted"] = plans_result.rowcount
                logger.debug(f"Deleted {plans_result.rowcount} plans")
                
                # 9. Finally delete the project itself
                logger.debug(f"Deleting project {project_id}")
                project_result = db.execute(
                    text("DELETE FROM projects WHERE id = :project_id"),
                    {"project_id": project_id_str}
                )
                
                if project_result.rowcount == 0:
                    raise HTTPException(
                        status_code=404,
                        detail="Project not found or already deleted"
                    )
                
                # Commit the changes
                db.commit()
                
                logger.info(f"Successfully deleted project {project_id} ({project_name})")
                logger.info(f"Deletion stats: {deletion_stats}")
                
                return {
                    "success": True,
                    "message": "Project deleted successfully",
                    "project_id": str(project_id),
                    "project_name": project_name,
                    "deletion_stats": deletion_stats
                }
                
            except Exception as e:
                # Rollback on any error
                db.rollback()
                logger.error(f"Error during project deletion: {e}")
                raise HTTPException(
                    status_code=500,
                    detail=f"Failed to delete project: {str(e)}"
                )
                
        except HTTPException:
            # Re-raise HTTP exceptions as-is
            raise
        except Exception as e:
            logger.error(f"Unexpected error in delete_project_safely: {e}")
            raise HTTPException(
                status_code=500,
                detail=f"Unexpected error during project deletion: {str(e)}"
            )

# Create a singleton instance
project_deletion_service = ProjectDeletionService()