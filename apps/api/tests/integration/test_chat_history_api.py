import pytest
from unittest.mock import patch


def test_chat_history_endpoint_returns_chronological(test_client):
    # Mock DB-backed helper to return newest-first
    sample = [
        {"message": "", "response": "ai second", "is_user": False, "timestamp": "2025-09-14T10:02:00"},
        {"message": "user first", "response": "", "is_user": True, "timestamp": "2025-09-14T10:01:00"},
    ]

    with patch("routers.chat.get_chat_history", return_value=sample):
        res = test_client.get("/chat/history", params={"session_id": "sess-123", "limit": 50})
        assert res.status_code == 200
        data = res.json()
        # Should be reversed to chronological
        assert len(data) == 2
        assert data[0]["is_user"] is True
        assert data[0]["message"] == "user first"
        assert data[1]["is_user"] is False
        assert data[1]["response"] == "ai second"

