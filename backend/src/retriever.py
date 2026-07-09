"""
Day 3, 4 & 10: Custom Retriever with Hybrid Search (Graph + Vector), Abstention, and RBAC
"""

import re
from typing import List

from llama_index.core import VectorStoreIndex, QueryBundle
from llama_index.core.retrievers import BaseRetriever
from llama_index.core.schema import NodeWithScore, Document
from llama_index.vector_stores.postgres import PGVectorStore
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from sqlalchemy import make_url
from backend.settings import settings


class HybridGraphRetriever(BaseRetriever):
    def __init__(
        self,
        collection_names: List[str],
        embed_model: HuggingFaceEmbedding,
        builder=None,
        role: str = "operator",
        similarity_top_k: int = 3,
        abstention_distance_threshold: float = 0.8,
    ):
        self.url = make_url(settings.postgres_uri)
        self.collection_names = collection_names
        self.embed_model = embed_model
        self.similarity_top_k = similarity_top_k
        self.abstention_threshold = abstention_distance_threshold
        self.builder = builder
        self.role = role.lower()
        super().__init__()

    def _retrieve(self, query_bundle: QueryBundle) -> List[NodeWithScore]:
        query_text = query_bundle.query_str

        # 1. Vector Search across collections
        all_vector_nodes = []
        for coll_name in self.collection_names:
            try:
                vector_store = PGVectorStore.from_params(
                    database=self.url.database,
                    host=self.url.host,
                    password=self.url.password,
                    port=self.url.port,
                    user=self.url.username,
                    table_name=coll_name,
                    embed_dim=384,
                )
                index = VectorStoreIndex.from_vector_store(
                    vector_store, embed_model=self.embed_model
                )
                retriever = index.as_retriever(similarity_top_k=self.similarity_top_k)
                nodes = retriever.retrieve(query_bundle)
                all_vector_nodes.extend(nodes)
            except Exception as e:
                print(f"Warning: Could not search collection {coll_name}: {e}")

        # Filter chunks by RBAC
        # Operators cannot see compliance reports or regulations
        if self.role == "operator":
            filtered_nodes = []
            for n in all_vector_nodes:
                source = n.node.metadata.get("source", "").lower()
                text = n.node.get_content().lower()
                if (
                    "compliance" in source
                    or "regulation" in source
                    or "audit" in source
                ):
                    continue
                filtered_nodes.append(n)
            all_vector_nodes = filtered_nodes

        all_vector_nodes.sort(key=lambda x: x.score, reverse=True)
        top_nodes = all_vector_nodes[: self.similarity_top_k]

        # Abstention Check
        if top_nodes:
            best_score = top_nodes[0].score
            if best_score < 0.3:
                abstain_doc = Document(
                    text="[ABSTAIN] Escalate to engineer. Confidence too low."
                )
                return [NodeWithScore(node=abstain_doc, score=1.0)]

        # 2. Graph Traversal (Real Graph integration)
        if self.builder:
            entities = self.extract_entities_from_query(query_text)
            graph_contexts = []
            for entity in entities:
                context = self.query_graph_neighbors(entity)
                if context:
                    graph_contexts.append(context)

            if graph_contexts:
                combined_graph_text = "\n".join(graph_contexts)
                graph_doc = Document(
                    text=combined_graph_text,
                    metadata={"source": "Knowledge Graph", "doc_type": "GRAPH"},
                )
                top_nodes.append(NodeWithScore(node=graph_doc, score=1.0))

        return top_nodes

    def extract_entities_from_query(self, query: str) -> List[str]:
        """Extract equipment tags from the query for graph entry points."""
        tags = set(re.findall(r"[A-Z]{1,3}-\d{2,4}", query.upper()))
        return list(tags)

    def query_graph_neighbors(self, entity: str) -> str:
        """Returns 1-hop neighbors from the Knowledge Graph."""
        if not self.builder or not hasattr(self.builder, "G"):
            return ""

        resolved_id = self.builder.resolve_node_id(entity, "EQUIPMENT")

        if self.builder.G.has_node(resolved_id):
            context = f"Graph Context for {resolved_id}:\n"
            for _, target, data in self.builder.G.out_edges(resolved_id, data=True):
                target_node = self.builder.G.nodes[target]

                # Enforce Graph RBAC: Operators cannot see REGULATION nodes
                if self.role == "operator" and target_node.get("label") == "REGULATION":
                    continue

                rel = data.get("type", "RELATED_TO")
                date_str = (
                    f" (Date: {data.get('valid_from', '')})"
                    if "valid_from" in data
                    else ""
                )
                context += f"- {resolved_id} {rel} {target}{date_str}\n"
            return context
        return ""
