"""
Day 3 & 4: Custom Retriever with Hybrid Search (Graph + Vector) and Abstention Logic
"""
import os
import chromadb
from typing import List, Optional

from llama_index.core import VectorStoreIndex, QueryBundle
from llama_index.core.retrievers import BaseRetriever
from llama_index.core.schema import NodeWithScore, Document
from llama_index.vector_stores.chroma import ChromaVectorStore
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from llama_index.core import Settings

from src.mock_graph import query_graph_neighbors, extract_entities

class HybridGraphRetriever(BaseRetriever):
    def __init__(
        self, 
        chroma_db_path: str, 
        collection_names: List[str], 
        embed_model: HuggingFaceEmbedding,
        similarity_top_k: int = 3,
        abstention_distance_threshold: float = 0.8  # If distance > 0.8, abstain
    ):
        self.chroma_client = chromadb.PersistentClient(path=chroma_db_path)
        self.collection_names = collection_names
        self.embed_model = embed_model
        self.similarity_top_k = similarity_top_k
        self.abstention_threshold = abstention_distance_threshold
        super().__init__()
        
    def _retrieve(self, query_bundle: QueryBundle) -> List[NodeWithScore]:
        query_text = query_bundle.query_str
        
        # 1. Vector Search across collections
        all_vector_nodes = []
        for coll_name in self.collection_names:
            try:
                collection = self.chroma_client.get_collection(coll_name)
                if collection.count() == 0:
                    continue
                vector_store = ChromaVectorStore(chroma_collection=collection)
                index = VectorStoreIndex.from_vector_store(
                    vector_store, embed_model=self.embed_model
                )
                retriever = index.as_retriever(similarity_top_k=self.similarity_top_k)
                nodes = retriever.retrieve(query_bundle)
                all_vector_nodes.extend(nodes)
            except Exception as e:
                print(f"Warning: Could not search collection {coll_name}: {e}")
                
        # Sort by score (assuming lower score = lower distance for Chroma, 
        # but LlamaIndex converts it to similarity. Actually Chroma returns distance.
        # Let's see what LlamaIndex does. If LlamaIndex keeps it as similarity, higher is better.
        # If it passes Chroma's L2 distance directly, lower is better. 
        # Usually LlamaIndex does `1 - distance` for Chroma. Let's assume higher is better.
        # So low confidence is < (1 - threshold) -> < 0.2
        # We will sort descending by score.
        all_vector_nodes.sort(key=lambda x: x.score, reverse=True)
        top_nodes = all_vector_nodes[:self.similarity_top_k]
        
        # Abstention Check (Day 4)
        # If the best match has a poor score, return a special abstention node.
        # Note: Depending on metric, if score is similarity (0 to 1), < 0.2 is bad.
        # If score is distance, > 0.8 is bad. Let's check the score of the top node.
        if top_nodes:
            best_score = top_nodes[0].score
            # Heuristic: if score is very small (similarity) or very high (distance)
            if best_score < 0.3: # Assuming similarity
                abstain_doc = Document(text="[ABSTAIN] Escalate to engineer. Confidence too low.")
                return [NodeWithScore(node=abstain_doc, score=1.0)]

        # 2. Graph Traversal (Day 3)
        entities = extract_entities(query_text)
        graph_contexts = []
        for entity in entities:
            context = query_graph_neighbors(entity)
            if context:
                graph_contexts.append(context)
                
        # 3. Combine
        if graph_contexts:
            combined_graph_text = "\n".join(graph_contexts)
            graph_doc = Document(
                text=combined_graph_text,
                metadata={"source": "Knowledge Graph", "doc_type": "GRAPH"}
            )
            top_nodes.append(NodeWithScore(node=graph_doc, score=1.0))
            
        return top_nodes
