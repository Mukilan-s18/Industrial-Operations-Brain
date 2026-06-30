"""
Day 5: LangGraph RCA Agent
Orchestrates multi-step reasoning: Query Rewriting -> Retrieve Work Orders -> Retrieve SOPs -> Synthesize
Returns structured results with real metrics.
"""
import os
import time
from typing import TypedDict
from langgraph.graph import StateGraph, END
from llama_index.llms.gemini import Gemini
from llama_index.core import QueryBundle
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from dotenv import load_dotenv

load_dotenv()

from backend.src.retriever import HybridGraphRetriever
from backend.src.generator import generate_answer, GenerationResult
from backend.src.llm_utils import RateLimitedLLM


# Define State
from typing import Any

class RCAState(TypedDict):
    query: str
    graph_builder: Any
    user_role: str
    original_query: str
    work_orders_context: list
    sops_context: list
    final_answer: str
    status: str
    # Structured metrics
    contradiction_detected: bool
    contradiction_details: str
    sources: list
    faithfulness_score: float
    abstained: bool


# Singleton-style caching for expensive objects
_embed_model = None
_chroma_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "chroma_db"))


def get_embed_model():
    global _embed_model
    if _embed_model is None:
        _embed_model = HuggingFaceEmbedding(model_name="BAAI/bge-small-en-v1.5")
    return _embed_model


def get_llm():
    return Gemini(model="models/gemini-2.5-flash-lite", api_key=os.getenv("GOOGLE_API_KEY"))


def get_retriever(collections: list[str], builder: Any, role: str):
    return HybridGraphRetriever(
        chroma_db_path=_chroma_path,
        collection_names=collections,
        embed_model=get_embed_model(),
        builder=builder,
        role=role
    )


# --- Nodes ---

def rewrite_query(state: RCAState):
    """Day 7: Query Rewriting for informal language."""
    llm = get_llm()
    safe_llm = RateLimitedLLM(llm)
    prompt = f"""Rewrite the following user query resolving any informal references to explicit equipment tags.
Known equipment tags: [P-101, HV-204, HV-205]
If the query already uses explicit tags, return it unchanged.
Return ONLY the rewritten query, nothing else.

Original Query: {state['original_query']}
Rewritten Query:"""
    response = safe_llm.complete(prompt)
    rewritten = str(response).strip()
    # Fallback: if LLM returns empty or garbage, use original
    if len(rewritten) < 3:
        rewritten = state['original_query']
    return {"query": rewritten, "status": f"Rewrote query to: {rewritten}"}


def retrieve_work_orders(state: RCAState):
    retriever = get_retriever(["work_orders"])
    nodes = retriever._retrieve(QueryBundle(state['query']))
    return {"work_orders_context": nodes, "status": "Searching past work orders..."}


def retrieve_sops(state: RCAState):
    retriever = get_retriever(["sops", "regulations"])
    nodes = retriever._retrieve(QueryBundle(state['query']))
    return {"sops_context": nodes, "status": "Searching SOPs and regulations..."}


def synthesize(state: RCAState):
    llm = get_llm()
    all_nodes = state.get('work_orders_context', []) + state.get('sops_context', [])
    result: GenerationResult = generate_answer(state['query'], all_nodes, llm)
    return {
        "final_answer": result.answer,
        "contradiction_detected": result.contradiction_detected,
        "contradiction_details": result.contradiction_details,
        "sources": result.sources,
        "faithfulness_score": result.faithfulness_score,
        "abstained": result.abstained,
        "status": "Synthesized final RCA."
    }


# --- Build Graph ---
def build_rca_graph():
    workflow = StateGraph(RCAState)

    workflow.add_node("rewrite", rewrite_query)
    workflow.add_node("get_wo", retrieve_work_orders)
    workflow.add_node("get_sops", retrieve_sops)
    workflow.add_node("synthesize", synthesize)

    workflow.set_entry_point("rewrite")
    workflow.add_edge("rewrite", "get_wo")
    workflow.add_edge("get_wo", "get_sops")
    workflow.add_edge("get_sops", "synthesize")
    workflow.add_edge("synthesize", END)

    return workflow.compile()


# Example runner
if __name__ == "__main__":
    app = build_rca_graph()
    inputs = {"original_query": "failures related to that pump leaking", "query": ""}

    for output in app.stream(inputs):
        for key, value in output.items():
            print(f"[{key}] {value.get('status', '')}")
            if "final_answer" in value:
                print(f"\nFinal RCA:\n{value['final_answer']}")
                print(f"Contradiction: {value.get('contradiction_detected', False)}")
                print(f"Faithfulness: {value.get('faithfulness_score', 0)}")
                print(f"Sources: {value.get('sources', [])}")
