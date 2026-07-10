import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, AsyncMock, MagicMock
from backend.app import app
from backend.dependencies import get_current_user

client = TestClient(app)


def mock_get_current_user():
    return {"username": "test", "role": "operator"}


def mock_get_current_user_engineer():
    return {"username": "test", "role": "engineer"}


@patch("backend.routers.chat.redis_client.get", new_callable=AsyncMock)
@patch("backend.routers.chat.redis_client.setex", new_callable=AsyncMock)
def test_chat_endpoint_operator_blocked(mock_setex, mock_get):
    app.dependency_overrides[get_current_user] = mock_get_current_user
    response = client.post("/chat", json={"query": "audit log"})
    assert response.status_code == 403
    app.dependency_overrides = {}


@patch("backend.routers.chat.redis_client.get", new_callable=AsyncMock)
@patch("backend.routers.chat.redis_client.setex", new_callable=AsyncMock)
@patch("backend.routers.chat.rca_graph.ainvoke", new_callable=AsyncMock)
@patch("backend.routers.chat.rca_graph.get_state")
def test_chat_endpoint_engineer_allowed(
    mock_get_state, mock_ainvoke, mock_setex, mock_get
):
    mock_get.return_value = None
    mock_ainvoke.return_value = {"final_answer": "Here is the audit log", "sources": []}

    mock_state = MagicMock()
    mock_state.next = []
    mock_get_state.return_value = mock_state

    app.dependency_overrides[get_current_user] = mock_get_current_user_engineer
    response = client.post("/chat", json={"query": "audit log"})
    assert response.status_code == 200
    assert response.json()["answer"] == "Here is the audit log"
    app.dependency_overrides = {}


@patch("backend.routers.graph.builder")
def test_graph_endpoints_available(mock_builder):
    mock_builder.get_graph_stats.return_value = {"node_count": 5, "edge_count": 2}
    response = client.get("/api/stats")
    assert response.status_code == 200


def test_toggle_fallback():
    response = client.post("/fallback/toggle?enabled=true")
    assert response.status_code == 200
    assert response.json() == {"fallback_mode": True}
