import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch
from backend.app import app

client = TestClient(app)


def test_metrics_endpoint():
    response = client.get("/metrics")
    assert response.status_code == 200
    data = response.json()
    assert "corpus_coverage_pct" in data


@patch("backend.routers.graph.builder")
def test_graph_viz_endpoint(mock_builder):
    import networkx as nx

    mock_builder.G = nx.DiGraph()
    mock_builder.G.add_node("test", label="EQUIPMENT")
    response = client.get("/api/graph-viz")
    assert response.status_code == 200


@patch("backend.routers.graph.builder")
def test_graph_nodes_and_edges(mock_builder):
    import networkx as nx

    mock_builder.G = nx.DiGraph()
    mock_builder.G.add_node("n1", label="EQUIPMENT")
    mock_builder.G.add_edge("n1", "n2", type="HAS_FAILURE")
    response_nodes = client.get("/api/nodes")
    response_edges = client.get("/api/edges")
    assert response_nodes.status_code == 200
    assert response_edges.status_code == 200


def test_read_root():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"status": "API Online"}
