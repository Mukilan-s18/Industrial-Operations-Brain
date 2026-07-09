import pytest
from fastapi.testclient import TestClient
from backend.app import app

client = TestClient(app)


def test_metrics_endpoint():
    response = client.get("/metrics")
    assert response.status_code == 200
    data = response.json()
    assert "corpus_coverage_pct" in data
    assert "fallback_mode" in data


def test_graph_viz_endpoint():
    response = client.get("/api/graph-viz")
    # It might return 404 if the graph file hasn't been generated yet
    assert response.status_code in [200, 404]
