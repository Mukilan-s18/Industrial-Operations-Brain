import pytest
from unittest.mock import MagicMock, patch
from backend.src.generator import (
    check_contradictions,
    compute_faithfulness,
    generate_answer,
    GenerationResult,
)
from llama_index.core.schema import NodeWithScore, Document


def test_check_contradictions_less_than_two_nodes():
    node = NodeWithScore(node=Document(text="val1"))
    has_contra, details = check_contradictions([node], MagicMock())
    assert has_contra is False
    assert details == ""


@patch("backend.src.generator.RateLimitedLLM")
def test_check_contradictions_yes(mock_safe_llm):
    mock_instance = MagicMock()
    mock_safe_llm.return_value = mock_instance
    mock_instance.complete.return_value = "CONTRADICTION: YES\nDETAILS: values clash"

    nodes = [
        NodeWithScore(node=Document(text="v1")),
        NodeWithScore(node=Document(text="v2")),
    ]
    has_contra, details = check_contradictions(nodes, MagicMock())

    assert has_contra is True
    assert details == "values clash"


@patch("backend.src.generator.RateLimitedLLM")
def test_check_contradictions_yes_alternate_format(mock_safe_llm):
    mock_instance = MagicMock()
    mock_safe_llm.return_value = mock_instance
    mock_instance.complete.return_value = "YES this is contradictory"

    nodes = [
        NodeWithScore(node=Document(text="v1")),
        NodeWithScore(node=Document(text="v2")),
    ]
    has_contra, details = check_contradictions(nodes, MagicMock())

    assert has_contra is True
    assert details == ""


@patch("backend.src.generator.RateLimitedLLM")
def test_check_contradictions_no(mock_safe_llm):
    mock_instance = MagicMock()
    mock_safe_llm.return_value = mock_instance
    mock_instance.complete.return_value = "CONTRADICTION: NO"

    nodes = [
        NodeWithScore(node=Document(text="v1")),
        NodeWithScore(node=Document(text="v2")),
    ]
    has_contra, details = check_contradictions(nodes, MagicMock())

    assert has_contra is False
    assert details == ""


def test_compute_faithfulness_empty():
    assert compute_faithfulness("", []) == 0.0


def test_compute_faithfulness_overlap():
    nodes = [NodeWithScore(node=Document(text="The quick brown fox jumps"))]
    answer = "The quick brown fox is fast"
    # non stopwords: quick brown fox fast
    # overlap: quick brown fox
    # grounded = 3 / 4 = 0.75
    score = compute_faithfulness(answer, nodes)
    assert score == 0.75


def test_compute_faithfulness_no_valid_words():
    nodes = [NodeWithScore(node=Document(text="The quick brown fox jumps"))]
    answer = "The the is are"  # all stopwords
    score = compute_faithfulness(answer, nodes)
    assert score == 0.0


def test_generate_answer_abstain():
    nodes = [NodeWithScore(node=Document(text="[ABSTAIN] escalate"))]
    res = generate_answer("q", nodes, MagicMock())
    assert res.abstained is True
    assert res.faithfulness_score == 0.0
    assert "Escalate to engineer" in res.answer


@patch("backend.src.generator.check_contradictions")
@patch("backend.src.generator.RateLimitedLLM")
def test_generate_answer_normal(mock_safe_llm, mock_check):
    mock_check.return_value = (False, "")
    mock_instance = MagicMock()
    mock_safe_llm.return_value = mock_instance
    mock_instance.complete.return_value = "This is the answer."

    nodes = [
        NodeWithScore(
            node=Document(
                text="This is context", metadata={"source": "man1", "revision": "A"}
            ),
            score=0.9,
        )
    ]
    res = generate_answer("query", nodes, MagicMock(), mode="brief")

    assert res.answer == "This is the answer."
    assert res.contradiction_detected is False
    assert len(res.sources) == 1
    assert res.sources[0]["doc"] == "man1"


@patch("backend.src.generator.check_contradictions")
@patch("backend.src.generator.RateLimitedLLM")
def test_generate_answer_with_contradiction(mock_safe_llm, mock_check):
    mock_check.return_value = (True, "conflict")
    mock_instance = MagicMock()
    mock_safe_llm.return_value = mock_instance
    mock_instance.complete.return_value = "Contradictory answer."

    nodes = [NodeWithScore(node=Document(text="context"))]
    res = generate_answer("query", nodes, MagicMock(), mode="detailed")

    assert res.contradiction_detected is True
    assert res.contradiction_details == "conflict"
