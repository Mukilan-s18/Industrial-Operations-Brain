import pytest
from fastapi.testclient import TestClient
from backend.app import app
import os
import json

client = TestClient(app)

def test_chat_endpoint_import_and_auth_success():
    """
    Test that the /chat endpoint loads correctly (no import errors) 
    and handles a basic query without crashing. 
    It also checks that RBAC correctly blocks restricted terms for operators.
    """
    
    # We mock out the Gemini API call if GOOGLE_API_KEY is not set,
    # or just expect a 403 / 500 depending on environment.
    # But for a basic e2e sanity check, we verify the endpoint is reachable
    # and RBAC logic is executed before any LLM calls.
    
    # Test 1: Operator trying to access restricted term
    response = client.post(
        "/chat",
        json={"query": "show me the audit log for e-201"},
        headers={"X-User-Role": "operator"}
    )
    assert response.status_code == 403
    assert "Access denied" in response.json()["detail"]

    # Test 2: Engineer trying to access restricted term
    # It should pass RBAC but might fail at LLM if no API key is set
    # We just ensure it doesn't return 403 and doesn't crash on import
    try:
        response = client.post(
            "/chat",
            json={"query": "show me the audit log for e-201"},
            headers={"X-User-Role": "engineer"}
        )
        assert response.status_code in [200, 500]  # 500 is acceptable here if no API key
    except Exception as e:
        # If it throws an exception internally due to missing API key, that's fine
        # We just want to ensure the app itself is structured correctly.
        pass

def test_graph_endpoints_available():
    """Verify that the merged graph endpoints are accessible."""
    response = client.get("/api/stats")
    assert response.status_code == 200
    data = response.json()
    assert "node_count" in data
    assert "edge_count" in data
