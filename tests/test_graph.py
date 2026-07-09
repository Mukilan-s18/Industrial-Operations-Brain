import pytest
from backend.src.ner_pipeline import NERPipeline
from backend.src.graph_builder import KnowledgeGraphBuilder


@pytest.fixture
def mock_docs():
    return [
        {
            "doc_id": "DOC-001",
            "title": "Maintenance Log - Pump P-101 Seal Failure",
            "author": "Rajesh Kumar",
            "date": "2025-05-10",
            "content": "Technician Rajesh Kumar checked Pump P-101. The unit experienced a severe seal leak causing a discharge pressure drop. We replaced the mechanical seal. Ref: OEM Manual Section 3.2.",
        },
        {
            "doc_id": "DOC-002",
            "title": "Compliance Audit Report",
            "author": "Sanjay Mehta",
            "date": "2025-06-01",
            "content": "Compliance check with OISD-118 regulations. Pump P-101 was inspected on 2025-06-01. However, Pump P-102 was found with an outdated inspection record (last inspection: 2024-03-15). Under OISD-118, all pumps handling hydrocarbons must undergo inspections at least every 365 days. Pump P-102 currently has a compliance gap. Also, Compressor C-201, governed by PESO guidelines, is pending inspection. Its last recorded inspection was on 2024-02-10.",
        },
    ]


def test_graph_building_and_queries(mock_docs):
    pipeline = NERPipeline()
    builder = KnowledgeGraphBuilder()

    nodes, edges = builder.build_graph_from_extracted_data(mock_docs, pipeline)

    assert nodes > 0
    assert edges > 0

    # Verify graph contains expected node labels
    assert builder.G.has_node("P-101")
    assert builder.G.nodes["P-101"]["label"] == "EQUIPMENT"

    assert builder.G.has_node("OISD-118")
    assert builder.G.nodes["OISD-118"]["label"] == "REGULATION"

    # Verify compliance gaps query (using current date 2025-09-01)
    gaps = builder.get_compliance_gaps("2025-09-01")

    # P-102 last inspected 2024-03-15 (more than 365 days before 2025-09-01)
    # C-201 last inspected 2024-02-10 (more than 365 days before 2025-09-01)
    # P-101 last inspected 2025-06-01 (less than 365 days before 2025-09-01)
    gap_equip_ids = [g["equipment_id"] for g in gaps]
    assert "P-102" in gap_equip_ids
    assert "C-201" in gap_equip_ids
    assert "P-101" not in gap_equip_ids

    # Verify stats
    stats = builder.get_graph_stats()
    assert stats["node_count"] == nodes
    assert stats["edge_count"] == edges
    assert "EQUIPMENT" in stats["nodes_by_type"]
    assert "REGULATION" in stats["nodes_by_type"]
