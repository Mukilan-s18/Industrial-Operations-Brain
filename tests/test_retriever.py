import pytest
from unittest.mock import patch, MagicMock
from backend.src.retriever import HybridGraphRetriever
from llama_index.core.schema import NodeWithScore, Document


def test_hybrid_graph_retriever_operator_filter():
    mock_embed = MagicMock()
    mock_builder = MagicMock()

    with patch("backend.src.retriever.make_url"):
        with patch("backend.src.retriever.PGVectorStore.from_params") as mock_pg:
            with patch(
                "backend.src.retriever.VectorStoreIndex.from_vector_store"
            ) as mock_index:
                # Mock index return
                mock_retriever = MagicMock()
                mock_index.return_value.as_retriever.return_value = mock_retriever

                # Mock retrieve nodes
                allowed_doc = Document(text="valid info", metadata={"source": "manual"})
                blocked_doc = Document(
                    text="secret audit", metadata={"source": "compliance audit"}
                )

                mock_node_allowed = NodeWithScore(node=allowed_doc, score=0.9)
                mock_node_blocked = NodeWithScore(node=blocked_doc, score=0.95)

                mock_retriever.retrieve.return_value = [
                    mock_node_allowed,
                    mock_node_blocked,
                ]

                retriever = HybridGraphRetriever(
                    collection_names=["docs"],
                    embed_model=mock_embed,
                    builder=mock_builder,
                    role="operator",
                )

                mock_bundle = MagicMock()
                mock_bundle.query_str = "how to fix pump?"

                # We need to bypass the graph builder for this test to just test the vector part
                retriever.builder = None

                nodes = retriever._retrieve(mock_bundle)
                assert len(nodes) == 1
                assert nodes[0].node.get_content() == "valid info"


def test_hybrid_graph_retriever_abstention():
    mock_embed = MagicMock()
    with patch("backend.src.retriever.make_url"):
        with patch("backend.src.retriever.PGVectorStore.from_params"):
            with patch(
                "backend.src.retriever.VectorStoreIndex.from_vector_store"
            ) as mock_index:
                mock_retriever = MagicMock()
                mock_index.return_value.as_retriever.return_value = mock_retriever

                low_score_doc = Document(text="unrelated")
                mock_node = NodeWithScore(node=low_score_doc, score=0.2)
                mock_retriever.retrieve.return_value = [mock_node]

                retriever = HybridGraphRetriever(
                    collection_names=["docs"], embed_model=mock_embed, role="engineer"
                )

                nodes = retriever._retrieve(MagicMock())
                assert len(nodes) == 1
                assert "[ABSTAIN]" in nodes[0].node.get_content()


def test_hybrid_graph_retriever_graph_integration():
    mock_embed = MagicMock()
    mock_builder = MagicMock()

    with patch("backend.src.retriever.make_url"):
        with patch("backend.src.retriever.PGVectorStore.from_params"):
            with patch(
                "backend.src.retriever.VectorStoreIndex.from_vector_store"
            ) as mock_index:
                mock_retriever = MagicMock()
                mock_index.return_value.as_retriever.return_value = mock_retriever

                valid_doc = Document(text="info")
                mock_node = NodeWithScore(node=valid_doc, score=0.9)
                mock_retriever.retrieve.return_value = [mock_node]

                # Mock graph traversal
                mock_builder.G.has_node.return_value = True
                mock_builder.G.out_edges.return_value = [
                    (
                        "PUMP-01",
                        "VALVE-02",
                        {"type": "CONNECTED_TO", "valid_from": "2023"},
                    )
                ]
                mock_builder.G.nodes = {"VALVE-02": {"label": "EQUIPMENT"}}
                mock_builder.resolve_node_id.return_value = "PUMP-01"

                retriever = HybridGraphRetriever(
                    collection_names=["docs"],
                    embed_model=mock_embed,
                    builder=mock_builder,
                    role="engineer",
                )

                mock_bundle = MagicMock()
                mock_bundle.query_str = "fix PUMP-01"

                nodes = retriever._retrieve(mock_bundle)
                # Should have 2 nodes: 1 vector, 1 graph
                assert len(nodes) == 2
                graph_node = nodes[1]
                assert "Graph Context for PUMP-01" in graph_node.node.get_content()


def test_pgvector_exception_handling():
    mock_embed = MagicMock()
    with patch("backend.src.retriever.make_url"):
        with patch(
            "backend.src.retriever.PGVectorStore.from_params",
            side_effect=Exception("DB Error"),
        ):
            retriever = HybridGraphRetriever(
                collection_names=["docs"], embed_model=mock_embed, role="engineer"
            )
            retriever.builder = None
            nodes = retriever._retrieve(MagicMock())
            # Should return empty list, handled by try-except
            assert len(nodes) == 0


def test_query_graph_neighbors_operator_blocked_regulation():
    mock_builder = MagicMock()
    mock_builder.G.has_node.return_value = True
    mock_builder.G.out_edges.return_value = [("PUMP-01", "REG-123", {})]
    mock_builder.G.nodes = {"REG-123": {"label": "REGULATION"}}
    mock_builder.resolve_node_id.return_value = "PUMP-01"

    with patch("backend.src.retriever.make_url"):
        retriever = HybridGraphRetriever(
            collection_names=[], embed_model=None, builder=mock_builder, role="operator"
        )
        context = retriever.query_graph_neighbors("PUMP-01")
        # Ensure it skips the regulation node
        assert "REG-123" not in context


def test_query_graph_neighbors_no_builder():
    with patch("backend.src.retriever.make_url"):
        retriever = HybridGraphRetriever(collection_names=[], embed_model=None)
        context = retriever.query_graph_neighbors("PUMP-01")
        assert context == ""
