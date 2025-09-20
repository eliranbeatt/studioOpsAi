import pytest
from unittest.mock import patch


def test_trello_export_not_configured(test_client):
    payload = {
        "project_id": "proj_1",
        "project_name": "Test Project",
        "cards": [
            {"external_id": "c1", "title": "Do thing", "list_name": "To Do"}
        ],
    }

    # ensure_board_structure returns None when not configured
    with patch("routers.trello.trello_service.ensure_board_structure", return_value=None):
        res = test_client.post("/trello/export", json=payload)
        assert res.status_code == 503
        body = res.json()
        # Error middleware returns structured error; accept either shape
        assert (
            body.get("detail") == "Trello not configured"
            or "Trello not configured" in body.get("message", "")
        )


def test_trello_export_success(test_client):
    payload = {
        "project_id": "proj_2",
        "project_name": "Proj 2",
        "cards": [
            {"external_id": "c1", "title": "Card 1", "list_name": "To Do"},
            {"external_id": "c2", "title": "Card 2", "list_name": "In Progress"},
        ],
    }

    board = {
        "board_id": "board_123",
        "board_name": "StudioOps - Proj 2 (proj_2)",
        "board_url": "https://trello.com/b/board_123",
    }

    result = {"success": True, "created": 2, "updated": 0, "total": 2, "errors": []}

    with patch("routers.trello.trello_service.ensure_board_structure", return_value=board):
        with patch("routers.trello.trello_service.upsert_cards", return_value=result):
            res = test_client.post("/trello/export", json=payload)
            assert res.status_code == 200
            data = res.json()
            assert data["success"] is True
            assert data["board"]["id"] == "board_123"
            assert data["summary"]["created"] == 2
            assert data["summary"]["total"] == 2
            assert data["summary"]["errors"] == []
