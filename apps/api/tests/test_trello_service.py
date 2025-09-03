"""Tests for Trello service integration"""

import pytest
from unittest.mock import patch, MagicMock
from services.trello_service import TrelloService

def test_trello_service_initialization():
    """Test Trello service initialization with and without credentials"""
    
    # Test without credentials
    with patch.dict('os.environ', {}, clear=True):
        service = TrelloService()
        assert not service.is_configured()
    
    # Test with credentials
    with patch.dict('os.environ', {
        'TRELLO_API_KEY': 'test_key',
        'TRELLO_API_TOKEN': 'test_token'
    }, clear=True):
        service = TrelloService()
        assert service.is_configured()

def test_ensure_board_structure():
    """Test board structure creation"""
    service = TrelloService()
    
    # Test when not configured
    with patch.object(service, 'is_configured', return_value=False):
        result = service.ensure_board_structure('test_project', 'Test Project')
        assert result is None
    
    # Test when configured
    with patch.object(service, 'is_configured', return_value=True):
        result = service.ensure_board_structure('test_project', 'Test Project')
        assert result is not None
        assert 'board_id' in result
        assert 'board_name' in result
        assert 'lists' in result
        assert result['board_name'] == 'StudioOps - Test Project (test_project)'

def test_translate_list_name():
    """Test Hebrew to English list name translation"""
    service = TrelloService()
    
    # Test Hebrew translations
    assert service._translate_list_name('לעשות') == 'To Do'
    assert service._translate_list_name('בתהליך') == 'In Progress'
    assert service._translate_list_name('ביקורת') == 'Review'
    assert service._translate_list_name('הושלם') == 'Completed'
    
    # Test unknown names return as-is
    assert service._translate_list_name('Unknown') == 'Unknown'

def test_upsert_cards_not_configured():
    """Test upsert cards when Trello is not configured"""
    service = TrelloService()
    
    with patch.object(service, 'is_configured', return_value=False):
        result = service.upsert_cards('board_123', [{'title': 'Test Card'}])
        assert not result['success']
        assert result['error'] == 'Trello not configured'

def test_upsert_cards_success():
    """Test successful card upsert"""
    service = TrelloService()
    
    test_cards = [
        {'external_id': 'card_1', 'title': 'Test Card 1', 'list_name': 'To Do'},
        {'external_id': 'card_2', 'title': 'Test Card 2', 'list_name': 'In Progress'}
    ]
    
    with patch.object(service, 'is_configured', return_value=True):
        with patch('time.sleep'):  # Mock sleep to speed up test
            result = service.upsert_cards('board_123', test_cards)
            
            assert result['success']
            assert result['created'] == 2
            assert result['total'] == 2
            assert len(result['errors']) == 0

def test_upsert_cards_empty_list():
    """Test upsert cards with empty list"""
    service = TrelloService()
    
    with patch.object(service, 'is_configured', return_value=True):
        result = service.upsert_cards('board_123', [])
        
        assert result['success']
        assert result['created'] == 0
        assert result['updated'] == 0
        assert result['total'] == 0
        assert len(result['errors']) == 0

if __name__ == "__main__":
    pytest.main([__file__, "-v"])