"""Trello integration service for task export"""

from typing import Dict, List, Any, Optional
import os
import time
from datetime import datetime
from trello import TrelloClient
from trello.exceptions import TrelloUnauthorized, TrelloBadRequest
import logging

logger = logging.getLogger(__name__)

class TrelloService:
    """Service for Trello integration and task export"""
    
    def __init__(self):
        self.api_key = os.getenv('TRELLO_API_KEY')
        self.api_token = os.getenv('TRELLO_API_TOKEN')
        self.client = None
        
        if self.api_key and self.api_token:
            try:
                self.client = TrelloClient(
                    api_key=self.api_key,
                    api_secret=self.api_token
                )
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
            # Try to find existing board for this project
            board_name = f"{project_name} ({project_id})"
            existing_boards = self.client.list_boards()
            
            for board in existing_boards:
                if board.name == board_name:
                    logger.info(f"Found existing Trello board: {board.name}")
                    return self._get_board_structure(board)
            
            # Create new board
            board = self.client.add_board(board_name)
            logger.info(f"Created new Trello board: {board.name}")
            
            # Create standard lists
            lists_config = [
                ("לעשות", "To Do"),
                ("בתהליך", "In Progress"),
                ("ביקורת", "Review"),
                ("הושלם", "Completed")
            ]
            
            lists = {}
            for hebrew_name, english_name in lists_config:
                trello_list = board.add_list(hebrew_name, pos='bottom')
                lists[english_name.lower()] = {
                    'id': trello_list.id,
                    'name': hebrew_name,
                    'english_name': english_name
                }
            
            # Add custom fields for project tracking
            self._add_custom_fields(board)
            
            return {
                'board_id': board.id,
                'board_name': board.name,
                'board_url': board.url,
                'lists': lists,
                'created': True
            }
            
        except (TrelloUnauthorized, TrelloBadRequest) as e:
            logger.error(f"Trello API error: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error ensuring board structure: {e}")
            return None
    
    def _add_custom_fields(self, board):
        """Add custom fields to Trello board"""
        try:
            # Add custom fields for project management
            custom_fields = [
                {
                    'name': 'עלות',
                    'type': 'number',
                    'pos': 'top'
                },
                {
                    'name': 'זמן מוערך',
                    'type': 'number',  # hours
                    'pos': 'top'
                },
                {
                    'name': 'דחיפות',
                    'type': 'list',
                    'options': ['נמוכה', 'בינונית', 'גבוהה'],
                    'pos': 'top'
                }
            ]
            
            for field_config in custom_fields:
                try:
                    board.add_custom_field(
                        field_config['name'],
                        field_config['type'],
                        options=field_config.get('options', []),
                        pos=field_config.get('pos', 'bottom')
                    )
                except Exception as e:
                    logger.warning(f"Failed to add custom field {field_config['name']}: {e}")
                    
        except Exception as e:
            logger.warning(f"Failed to add custom fields: {e}")
    
    def _get_board_structure(self, board) -> Dict[str, Any]:
        """Get existing board structure"""
        lists = {}
        for trello_list in board.open_lists():
            lists[trello_list.name.lower()] = {
                'id': trello_list.id,
                'name': trello_list.name,
                'english_name': self._translate_list_name(trello_list.name)
            }
        
        return {
            'board_id': board.id,
            'board_name': board.name,
            'board_url': board.url,
            'lists': lists,
            'created': False
        }
    
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
            board = self.client.get_board(board_id)
            if not board:
                return {'success': False, 'error': 'Board not found', 'created': 0, 'updated': 0}
            
            created = 0
            updated = 0
            errors = []
            
            for card_data in cards_data:
                try:
                    result = self._upsert_card(board, card_data)
                    if result['created']:
                        created += 1
                    else:
                        updated += 1
                    
                    # Rate limiting
                    time.sleep(0.1)
                    
                except Exception as e:
                    errors.append(f"Card {card_data.get('title', 'unknown')}: {e}")
            
            return {
                'success': len(errors) == 0,
                'created': created,
                'updated': updated,
                'errors': errors,
                'total': len(cards_data)
            }
            
        except Exception as e:
            return {'success': False, 'error': str(e), 'created': 0, 'updated': 0}
    
    def _upsert_card(self, board, card_data: Dict[str, Any]) -> Dict[str, Any]:
        """Upsert a single card with idempotency"""
        external_id = card_data.get('external_id')
        
        # Try to find existing card by external ID
        existing_card = None
        if external_id:
            for card in board.open_cards():
                if card.name.startswith(f"[{external_id}]"):
                    existing_card = card
                    break
        
        if existing_card:
            # Update existing card
            self._update_card(existing_card, card_data)
            return {'created': False, 'card_id': existing_card.id}
        else:
            # Create new card
            new_card = self._create_card(board, card_data)
            return {'created': True, 'card_id': new_card.id}
    
    def _create_card(self, board, card_data: Dict[str, Any]):
        """Create a new Trello card"""
        list_name = card_data.get('list_name', 'To Do').lower()
        target_list = None
        
        # Find the target list
        for trello_list in board.open_lists():
            if trello_list.name.lower() == list_name:
                target_list = trello_list
                break
        
        if not target_list:
            # Fallback to first list
            target_list = board.open_lists()[0]
        
        # Create card title with external ID for idempotency
        external_id = card_data.get('external_id', '')
        title_prefix = f"[{external_id}]" if external_id else ""
        card_title = f"{title_prefix} {card_data['title']}".strip()
        
        # Create card
        card = target_list.add_card(
            name=card_title,
            desc=card_data.get('description', ''),
            due=card_data.get('due_date')
        )
        
        # Add labels
        if 'labels' in card_data:
            for label_name in card_data['labels']:
                try:
                    card.add_label(label_name)
                except:
                    pass  # Label might not exist
        
        # Add checklist
        if 'checklist' in card_data:
            checklist = card.add_checklist('פריטים לביצוע', card_data['checklist'])
        
        logger.info(f"Created Trello card: {card_title}")
        return card
    
    def _update_card(self, card, card_data: Dict[str, Any]):
        """Update an existing Trello card"""
        # Update basic fields
        if 'description' in card_data:
            card.set_description(card_data['description'])
        
        if 'due_date' in card_data:
            card.set_due(card_data['due_date'])
        
        # Move to different list if specified
        if 'list_name' in card_data:
            try:
                board = card.board
                target_list = None
                for trello_list in board.open_lists():
                    if trello_list.name.lower() == card_data['list_name'].lower():
                        target_list = trello_list
                        break
                
                if target_list and target_list.id != card.list_id:
                    card.change_list(target_list.id)
            except Exception as e:
                logger.warning(f"Failed to move card to list: {e}")
        
        logger.info(f"Updated Trello card: {card.name}")

# Global instance
trello_service = TrelloService()