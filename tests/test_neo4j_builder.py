import pytest
import os
from unittest.mock import MagicMock, patch
from backend.src.neo4j_builder import Neo4jBuilder


@pytest.fixture
def mock_driver():
    with patch("backend.src.neo4j_builder.GraphDatabase.driver") as mock_driver:
        mock_instance = MagicMock()
        mock_driver.return_value = mock_instance
        yield mock_instance


@pytest.fixture
def builder(mock_driver):
    with patch("os.path.exists", return_value=False):
        b = Neo4jBuilder(config_path="dummy")
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


def test_close(builder, mock_driver):
    builder.close()
    mock_driver.close.assert_called_once()


def test_execute_write(builder, mock_driver):
    mock_session = MagicMock()
    mock_driver.session.return_value.__enter__.return_value = mock_session
    builder._execute_write("QUERY")
    mock_session.run.assert_called_once_with("QUERY", {})


def test_execute_read(builder, mock_driver):
    mock_session = MagicMock()
    mock_driver.session.return_value.__enter__.return_value = mock_session
    mock_session.run.return_value.data.return_value = [{"k": "v"}]
    res = builder._execute_read("QUERY")
    assert res == [{"k": "v"}]


def test_resolve_node_id(builder):
    builder.manual_mappings = {"PUMP1": "P-101"}

    # Manual mapping
    assert builder.resolve_node_id("PUMP1", "EQUIPMENT") == "P-101"

    # regex format normalization
    assert builder.resolve_node_id("p 101", "EQUIPMENT") == "P-101"

    # local cache
    builder._local_nodes["VALVE-200"] = "COMPONENT"
    assert builder.resolve_node_id("VALVE200", "COMPONENT") == "VALVE-200"

    # blocklist
    builder._local_nodes["P-101"] = "EQUIPMENT"
    assert builder.resolve_node_id("P-102", "EQUIPMENT") == "P-102"


@patch.object(Neo4jBuilder, "_execute_write")
def test_add_node(mock_write, builder):
    res_id = builder.add_node("N1", "EQUIPMENT", {"k": "v"})
    assert res_id == "N1"
    mock_write.assert_called_once()
    assert builder._local_nodes["N1"] == "EQUIPMENT"


@patch.object(Neo4jBuilder, "_execute_write")
def test_add_edge(mock_write, builder):
    builder.add_edge("N1", "N2", "CONNECTED")
    mock_write.assert_called_once()


@patch.object(Neo4jBuilder, "add_node")
@patch.object(Neo4jBuilder, "add_edge")
@patch.object(Neo4jBuilder, "_execute_read")
def test_build_graph_from_extracted_data(
    mock_read, mock_add_edge, mock_add_node, builder
):
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
    mock_ner.extract_entities.return_value = [ent1, ent2, ent3]

    # Mock spaCy sentences
    mock_sent = MagicMock()
    mock_sent.start_char = 0
    mock_sent.end_char = 100
    mock_sent.text = "P-101 has severe leakage. Checked on 2023-01-02."
    mock_doc = MagicMock()
    mock_doc.sents = [mock_sent]
    mock_ner.nlp.return_value = mock_doc

    mock_read.return_value = [{"nodes": 5}]

    n_nodes, n_edges = builder.build_graph_from_extracted_data(docs, mock_ner)

    assert n_nodes == 5
    assert n_edges == 0
    mock_add_node.assert_called()
    mock_add_edge.assert_called()


@patch.object(Neo4jBuilder, "_execute_read")
def test_get_compliance_gaps(mock_read, builder):
    mock_read.return_value = [{"equipment_id": "P-101"}]
    res = builder.get_compliance_gaps("2023-05-01")
    assert len(res) == 1

    # Test without date
    res = builder.get_compliance_gaps()
    assert len(res) == 1


@patch.object(Neo4jBuilder, "_execute_read")
def test_get_failure_patterns(mock_read, builder):
    mock_read.return_value = [{"equipment_id": "P-101"}]
    res = builder.get_failure_patterns()
    assert len(res) == 1


@patch.object(Neo4jBuilder, "_execute_read")
def test_get_graph_stats(mock_read, builder):
    mock_read.return_value = [{"c": 10}]
    stats = builder.get_graph_stats()
    assert stats["node_count"] == 10
    assert stats["edge_count"] == 10
