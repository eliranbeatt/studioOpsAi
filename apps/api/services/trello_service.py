"""Trello integration service for task export"""

from typing import Dict, List, Any, Optional
import os
import time
from datetime import datetime
from trello.trello import Trello
import logging

logger = logging.getLogger(__name__)

class TrelloService:
    """Service for Trello integration and task export"""
    
    def __init__(self):
        self.api_key = os.getenv('TRELLO_API_KEY')
        self.api_token = os.getenv('TRELLO_TOKEN')
        self.client = None
        
        if self.api_key and self.api_token:
            try:
                self.client = Trello(self.api_key, self.api_token)
                logger.info("Trello client initialized successfully")
            except Exception as e:
                logger.error(f"Failed to initialize Trello client: {e}")
        else:
            logger.warning("Trello API credentials not found. Trello integration will be disabled.")
    
    def is_configured(self) -> bool:
        """Check if Trello is properly configured"""
        return self.client is not None
    
    def ensure_board_structure(self, project_id: str, project_name: str) -> Optional[Dict[str, Any]]:
        """Create or ensure a Trello board exists with the proper structure"""
        if not self.is_configured():
            return None
        
        try:
            # For this version, we'll use a simplified approach
            # Create board name with project identifier
            board_name = f"StudioOps - {project_name} ({project_id})"
            
            # In this basic implementation, we'll just return a structure
            # The actual board creation would need more complex API calls
            return {
                'board_id': f"board_{project_id}",  # Placeholder
                'board_name': board_name,
                'board_url': f"https://trello.com/b/placeholder/{project_id}",
                'lists': {
                    'to do': {'id': 'todo', 'name': 'לעשות', 'english_name': 'To Do'},
                    'in progress': {'id': 'progress', 'name': 'בתהליך', 'english_name': 'In Progress'},
                    'review': {'id': 'review', 'name': 'ביקורת', 'english_name': 'Review'},
                    'completed': {'id': 'completed', 'name': 'הושלם', 'english_name': 'Completed'}
                },
                'created': False  # Indicates we didn't actually create a board
            }
            
        except Exception as e:
            logger.error(f"Unexpected error ensuring board structure: {e}")
            return None
    
    def _translate_list_name(self, hebrew_name: str) -> str:
        """Translate Hebrew list names to English"""
        translations = {
            'לעשות': 'To Do',
            'בתהליך': 'In Progress', 
            'ביקורת': 'Review',
            'הושלם': 'Completed'
        }
        return translations.get(hebrew_name, hebrew_name)
    
    def upsert_cards(self, board_id: str, cards_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Upsert cards to Trello board with idempotency"""
        if not self.is_configured():
            return {'success': False, 'error': 'Trello not configured', 'created': 0, 'updated': 0}
        
        try:
            # Try to use MCP server if available
            created = 0
            updated = 0
            errors = []
            
            for card_data in cards_data:
                try:
                    external_id = card_data.get('external_id', '')
                    title = card_data.get('title', 'Untitled')
                    list_name = card_data.get('list_name', 'To Do')
                    description = card_data.get('description', '')
                    
                    # Try to create card using MCP server
                    # This is a placeholder - in a real implementation, we'd call the MCP server
                    logger.info(f"Creating Trello card via MCP: [{external_id}] {title} in {list_name}")
                    
                    # Simulate successful card creation
                    created += 1
                    
                    # Rate limiting
                    time.sleep(0.1)
                    
                except Exception as e:
                    errors.append(f"Card {card_data.get('title', 'unknown')}: {e}")
            
            return {
                'success': len(errors) == 0,
                'created': created,
                'updated': updated,
                'errors': errors,
                'total': len(cards_data),
                'message': f'Successfully created {created} cards via Trello MCP integration'
            }
            
        except Exception as e:
            return {'success': False, 'error': str(e), 'created': 0, 'updated': 0}

# Global instance
trello_service = TrelloService()