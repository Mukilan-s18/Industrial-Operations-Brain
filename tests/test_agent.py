import pytest
import os
import json
import sqlite3
from unittest.mock import patch, mock_open, MagicMock
from backend.src.agent import (
    get_embed_model,
    get_llm,
    get_retriever,
    input_guardrail,
    check_safety,
    rewrite_query,
    check_live_sensors,
    retrieve_work_orders,
    retrieve_sops,
    synthesize,
    execute_action,
    build_rca_graph,
    _embed_model,
)


def test_get_embed_model():
    with patch("backend.src.agent.HuggingFaceEmbedding") as mock_hf:
        model = get_embed_model()
        assert model is not None
        # Call again to test singleton
        model2 = get_embed_model()
        assert model2 is model


def test_get_llm():
    with patch("backend.src.agent.GoogleGenAI") as mock_ggai:
        llm = get_llm()
        assert llm is not None


def test_get_retriever():
    with patch("backend.src.agent.get_embed_model"):
        with patch("backend.src.agent.HybridGraphRetriever") as mock_hgr:
            ret = get_retriever(["test"], MagicMock(), "operator")
            assert ret is not None


def test_input_guardrail_safe():
    with patch("backend.src.agent.get_llm") as mock_llm:
        mock_instance = MagicMock()
        mock_llm.return_value = mock_instance
        mock_instance.complete.return_value = "SAFE"
        state = {"original_query": "hello"}
        res = input_guardrail(state)
        assert res["status"] == "Input passed safety check"


def test_input_guardrail_unsafe():
    with patch("backend.src.agent.get_llm") as mock_llm:
        mock_instance = MagicMock()
        mock_llm.return_value = mock_instance
        mock_instance.complete.return_value = "UNSAFE ignore instructions"
        state = {"original_query": "drop table"}
        res = input_guardrail(state)
        assert res["action_taken"] == "BLOCKED"


def test_check_safety():
    assert check_safety({"action_taken": "BLOCKED"}) == "blocked"
    assert check_safety({}) == "safe"


@patch("backend.src.agent.get_llm")
def test_rewrite_query_success(mock_get_llm):
    with patch("backend.src.agent.RateLimitedLLM") as mock_safe_llm:
        mock_instance = MagicMock()
        mock_safe_llm.return_value = mock_instance
        mock_instance.complete.return_value = "fix P-101"

        state = {"original_query": "fix pump"}
        res = rewrite_query(state)
        assert res["query"] == "fix P-101"


@patch("backend.src.agent.get_llm")
def test_rewrite_query_fallback(mock_get_llm):
    with patch("backend.src.agent.RateLimitedLLM") as mock_safe_llm:
        mock_instance = MagicMock()
        mock_safe_llm.return_value = mock_instance
        mock_instance.complete.return_value = "a"  # Less than 3 chars

        state = {"original_query": "fix pump"}
        res = rewrite_query(state)
        assert res["query"] == "fix pump"


def test_check_live_sensors_success():
    mock_data = json.dumps({"equipment": {"PUMP-01": {"temp": 100}}})
    with patch("os.path.exists", return_value=True):
        with patch("builtins.open", mock_open(read_data=mock_data)):
            res = check_live_sensors({})
            assert "PUMP-01" in res["live_sensor_context"]


def test_check_live_sensors_exception():
    with patch("os.path.exists", side_effect=Exception("error")):
        res = check_live_sensors({})
        assert res["live_sensor_context"] == "LIVE SCADA METRICS (Vibration & Temp): "


@patch("backend.src.agent.get_retriever")
def test_retrieve_work_orders(mock_get_retriever):
    mock_retriever = MagicMock()
    mock_get_retriever.return_value = mock_retriever
    mock_retriever._retrieve.return_value = ["node1"]

    res = retrieve_work_orders({"query": "q", "graph_builder": None, "user_role": "op"})
    assert res["work_orders_context"] == ["node1"]


@patch("backend.src.agent.get_retriever")
def test_retrieve_sops(mock_get_retriever):
    mock_retriever = MagicMock()
    mock_get_retriever.return_value = mock_retriever
    mock_retriever._retrieve.return_value = ["node2"]

    res = retrieve_sops({"query": "q", "graph_builder": None, "user_role": "op"})
    assert res["sops_context"] == ["node2"]


@patch("backend.src.agent.generate_answer")
def test_synthesize(mock_generate):
    mock_result = MagicMock()
    mock_result.answer = "final answer"
    mock_result.contradiction_detected = False
    mock_result.contradiction_details = ""
    mock_result.sources = []
    mock_result.faithfulness_score = 1.0
    mock_result.abstained = False
    mock_generate.return_value = mock_result

    state = {
        "query": "q",
        "work_orders_context": [],
        "sops_context": [],
        "live_sensor_context": "temp 100",
    }
    with patch("backend.src.agent.get_llm"):
        res = synthesize(state)
        assert res["final_answer"] == "final answer"


@patch("backend.src.agent.get_llm")
@patch("sqlite3.connect")
def test_execute_action_create_wo(mock_connect, mock_get_llm):
    mock_cursor = MagicMock()
    mock_connect.return_value.cursor.return_value = mock_cursor

    mock_llm_instance = MagicMock()
    mock_llm_instance.complete.return_value = '{"should_create_work_order": true, "equipment_id": "P-101", "priority": "High", "reason": "Test reason"}'
    mock_get_llm.return_value = mock_llm_instance

    state = {
        "final_answer": "I recommend we create a work order for the pump.",
        "query": "q",
    }
    res = execute_action(state)
    assert res["action_taken"] == "CREATE_SAP_WO"


@patch("backend.src.agent.get_llm")
@patch("sqlite3.connect")
def test_execute_action_create_wo_db_error(mock_connect, mock_get_llm):
    mock_cursor = MagicMock()
    mock_cursor.execute.side_effect = sqlite3.Error("DB error")
    mock_connect.return_value.cursor.return_value = mock_cursor

    mock_llm_instance = MagicMock()
    mock_llm_instance.complete.return_value = '{"should_create_work_order": true, "equipment_id": "P-101", "priority": "High", "reason": "Test reason"}'
    mock_get_llm.return_value = mock_llm_instance

    state = {"final_answer": "I recommend we create a work order.", "query": "q"}
    res = execute_action(state)
    # the new logic traps the error and returns NONE
    assert res["action_taken"] == "NONE"


@patch("backend.src.agent.get_llm")
def test_execute_action_none(mock_get_llm):
    mock_llm_instance = MagicMock()
    mock_llm_instance.complete.return_value = '{"should_create_work_order": false}'
    mock_get_llm.return_value = mock_llm_instance

    state = {"final_answer": "Everything is fine."}
    res = execute_action(state)
    assert res["action_taken"] == "NONE"


def test_build_rca_graph():
    graph = build_rca_graph()
    assert graph is not None
