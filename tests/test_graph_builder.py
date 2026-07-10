import pytest
import os
import json
import networkx as nx
from unittest.mock import MagicMock, patch, mock_open
from backend.src.graph_builder import KnowledgeGraphBuilder


@pytest.fixture
def builder():
    # Use empty config to avoid file IO dependencies
    with patch("os.path.exists", return_value=False):
        b = KnowledgeGraphBuilder(config_path="dummy")
        b.equipment_rules = [
            {
                "pattern": "P-.*",
                "type": "Pump",
                "default_regulations": [
                    {
                        "id": "REG-1",
                        "label": "REGULATION",
                        "clause": "A",
                        "authority": "OSHA",
                    }
                ],
            }
        ]
        b.location_rules = [{"pattern": "P-.*", "location": "Pump Room"}]
        b.regulation_metadata = [
            {"pattern": "REG-.*", "clause": "B", "authority": "EPA", "interval": 180}
        ]
        b.blocklist = {"P-101": ["P-102"]}
        return b


def test_resolve_node_id(builder):
    builder.manual_mappings = {"PUMP1": "P-101"}

    # Manual mapping
    assert builder.resolve_node_id("PUMP1", "EQUIPMENT") == "P-101"

    # regex format normalization
    assert builder.resolve_node_id("p 101", "EQUIPMENT") == "P-101"

    # fuzzy matching
    builder.G.add_node("VALVE-200", label="COMPONENT")
    assert builder.resolve_node_id("VALVE200", "COMPONENT") == "VALVE-200"


def test_resolve_node_id_blocklist(builder):
    builder.G.add_node("P-101", label="EQUIPMENT")
    # Fuzzy match would normally catch it, but blocklist prevents it
    assert builder.resolve_node_id("P-102", "EQUIPMENT") == "P-102"


def test_add_node(builder):
    builder.add_node("N1", "EQUIPMENT", {"k": "v"})
    assert "N1" in builder.G

    # Merge existing
    builder.add_node("N1", "EQUIPMENT", {"k2": "v2"})
    assert builder.G.nodes["N1"]["k"] == "v"
    assert builder.G.nodes["N1"]["k2"] == "v2"


def test_add_edge(builder):
    builder.add_edge("N1", "N2", "CONNECTED")
    assert builder.G.has_edge("N1", "N2")

    # Increment weight
    builder.add_edge("N1", "N2", "CONNECTED")
    edges = builder.G["N1"]["N2"]
    edge_key = list(edges.keys())[0]
    assert edges[edge_key]["weight"] == 2


def test_build_graph_from_extracted_data(builder):
    docs = [
        {
            "doc_id": "D1",
            "title": "T",
            "author": "Auth",
            "date": "2023-01-01",
            "content": "P-101 has severe leakage. Checked on 2023-01-02.",
        }
    ]

    mock_ner = MagicMock()
    # Mock entities
    ent1 = MagicMock()
    ent1.id = "P-101"
    ent1.label = "EQUIPMENT"
    ent1.text = "P-101"
    ent1.properties = {}
    ent1.span_start = 0
    ent1.span_end = 5

    ent2 = MagicMock()
    ent2.id = "leakage"
    ent2.label = "FAILURE_MODE"
    ent2.text = "leakage"
    ent2.properties = {}
    ent2.span_start = 17
    ent2.span_end = 24

    ent3 = MagicMock()
    ent3.id = "2023-01-02"
    ent3.label = "DATE"
    ent3.text = "2023-01-02"
    ent3.properties = {}
    ent3.span_start = 37
    ent3.span_end = 47

    ent4 = MagicMock()
    ent4.id = "REG-1"
    ent4.label = "REGULATION"
    ent4.text = "REG-1"
    ent4.properties = {}
    ent4.span_start = 0
    ent4.span_end = 0

    ent5 = MagicMock()
    ent5.id = "PARAM"
    ent5.label = "PARAMETER"
    ent5.text = "PARAM"
    ent5.properties = {}
    ent5.span_start = 0
    ent5.span_end = 0
    mock_ner.extract_entities.return_value = [ent1, ent2, ent3, ent4, ent5]

    # Mock spaCy sentences
    mock_sent = MagicMock()
    mock_sent.start_char = 0
    mock_sent.end_char = 100
    mock_sent.text = "P-101 has severe leakage. Checked on 2023-01-02. REG-1 PARAM."
    mock_doc = MagicMock()
    mock_doc.sents = [mock_sent]
    mock_ner.nlp.return_value = mock_doc

    n_nodes, n_edges = builder.build_graph_from_extracted_data(docs, mock_ner)

    assert n_nodes > 0
    assert n_edges > 0
    assert "P-101" in builder.G
    assert "leakage" in builder.G
    assert builder.G.has_edge("P-101", "leakage")  # HAS_FAILURE
    assert builder.G.has_edge("P-101", "2023-01-02")  # HAS_INSPECTION
    assert builder.G.has_edge("P-101", "REG-1")  # GOVERNED_BY
    assert builder.G.has_edge("P-101", "PARAM")  # HAS_PARAMETER


def test_get_compliance_gaps(builder):
    builder.add_node("P-101", "EQUIPMENT")
    builder.add_node("REG-1", "REGULATION", {"inspection_interval_days": 30})
    builder.add_edge("P-101", "REG-1", "GOVERNED_BY")

    # Gap because no inspection
    gaps = builder.get_compliance_gaps("2023-05-01")
    assert len(gaps) == 1

    # Gap because overdue
    builder.add_edge("P-101", "2023-01-01", "HAS_INSPECTION")
    gaps2 = builder.get_compliance_gaps("2023-05-01")
    assert len(gaps2) == 1

    # No gap
    gaps3 = builder.get_compliance_gaps("2023-01-15")
    assert len(gaps3) == 0


def test_get_compliance_gaps_dynamic_date(builder):
    builder.add_node("P-101", "EQUIPMENT")
    builder.add_node("REG-1", "REGULATION", {"inspection_interval_days": 30})
    builder.add_edge("P-101", "REG-1", "GOVERNED_BY")
    builder.add_node("2023-01-01", "DATE")
    builder.add_node("D1", "DOCUMENT", {"date": "invalid"})

    # Tests the dynamic date logic
    gaps = builder.get_compliance_gaps()
    assert len(gaps) == 1


def test_get_compliance_gaps_dynamic_date_fallback(builder):
    builder.add_node("P-101", "EQUIPMENT")
    builder.add_node("REG-1", "REGULATION", {"inspection_interval_days": 30})
    builder.add_edge("P-101", "REG-1", "GOVERNED_BY")
    # No dates in graph
    gaps = builder.get_compliance_gaps()
    assert len(gaps) == 1


def test_get_failure_patterns(builder):
    builder.add_node("P-101", "EQUIPMENT")
    builder.add_node("D1", "DOCUMENT", {"title": "OEM Manual"})
    builder.add_edge("D1", "P-101", "MENTIONS")

    # Add 3 failure edges (weight 3)
    builder.add_edge("P-101", "leak", "HAS_FAILURE", properties={"weight": 3})

    patterns = builder.get_failure_patterns()
    assert len(patterns) == 1
    assert patterns[0]["count"] == 3
    assert len(patterns[0]["recommendations"]) == 1


def test_get_graph_stats(builder):
    builder.add_node("P-101", "EQUIPMENT")
    stats = builder.get_graph_stats()
    assert stats["node_count"] == 1
    assert stats["equipment_coverage_pct"] == 0.0


def test_save_load_graph(builder):
    builder.add_node("P-101", "EQUIPMENT")

    with patch("os.makedirs"):
        with patch("builtins.open", mock_open()) as m:
            builder.save_graph("test.json")
            m.assert_called_once()

    mock_data = json.dumps(nx.node_link_data(builder.G))
    with patch("builtins.open", mock_open(read_data=mock_data)):
        builder.load_graph("test.json")
        assert "P-101" in builder.G
