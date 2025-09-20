import pytest
from unittest.mock import patch


def test_chat_message_basic(test_client):
    with patch("routers.chat.get_project_context", return_value={"project_name": "DemoProj"}):
        with patch("routers.chat.get_chat_history", return_value=[{"message": "hi", "response": "yo", "is_user": True, "timestamp": "now"}]):
            with patch("routers.chat.search_rag_documents", return_value=[{"title": "Doc1", "content": "Some content", "type": "note"}]):
                with patch("llm_service.llm_service.generate_response", return_value={
                    "message": "Hello from LLM",
                    "session_id": "sess1",
                    "ai_enabled": False,
                    "mock_mode": True,
                }):
                    res = test_client.post("/chat/message", json={
                        "message": "Hello cabinet project",
                        "project_id": "proj",
                        "session_id": "sess1",
                    })
                    assert res.status_code == 200
                    data = res.json()
                    assert data["message"].startswith("Hello")
                    assert data["context"]["project"]["project_name"] == "DemoProj"
                    assert len(data["context"]["rag_documents"]) == 1


def test_chat_stream_sse(test_client):
    # Force a simple message so streaming yields content
    with patch("llm_service.llm_service.generate_response", return_value={
        "message": "Hello world",
        "session_id": "sess1",
        "ai_enabled": False,
        "mock_mode": True,
    }):
        res = test_client.post("/chat/stream", json={"message": "Hi"})
        assert res.status_code == 200
        assert res.headers.get("content-type", "").startswith("text/event-stream")
        # The streamed body contains SSE lines with 'data: '
        text = res.text
        assert "data: {" in text
