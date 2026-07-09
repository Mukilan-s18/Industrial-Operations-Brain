import os
import requests
import streamlit as st

API_BASE_URL = os.getenv("API_BASE_URL", "http://127.0.0.1:8000")


class MockG:
    @property
    def nodes(self):
        try:
            nodes_data = requests.get(f"{API_BASE_URL}/api/nodes").json()
            return [n["id"] for n in nodes_data]
        except requests.exceptions.RequestException as e:
            st.error(f"Error fetching nodes: {e}")
            return []


class MockBuilder:
    def __init__(self):
        self.G = MockG()

    def get_graph_stats(self):
        try:
            return requests.get(f"{API_BASE_URL}/api/stats").json()
        except requests.exceptions.RequestException as e:
            st.error(f"Error fetching graph stats: {e}")
            return {
                "node_count": 0,
                "edge_count": 0,
                "nodes_by_type": {},
                "equipment_coverage_pct": 0.0,
            }


class MockNER:
    def evaluate_accuracy(self):
        try:
            return requests.get(f"{API_BASE_URL}/api/ner-evaluation").json()
        except requests.exceptions.RequestException as e:
            st.error(f"Error evaluating NER: {e}")
            return {
                "accuracy": 0,
                "f1_score": 0,
                "precision": 0,
                "recall": 0,
                "details": [],
            }


def get_graph_viz(node_id=None, role=None):
    try:
        params = {}
        if node_id and node_id != "All Nodes":
            params["node_id"] = node_id
        if role:
            params["role"] = role
        res = requests.get(f"{API_BASE_URL}/api/graph-viz", params=params)
        res.raise_for_status()
        return res.text
    except requests.exceptions.RequestException as e:
        return f"<div style='color: white;'>Error loading graph visualization: {e}. Ensure backend is running.</div>"


builder = MockBuilder()
ner = MockNER()
