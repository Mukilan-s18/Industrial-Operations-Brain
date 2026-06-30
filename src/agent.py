"""
Day 5: LangGraph RCA Agent
Orchestrates multi-step reasoning: Query Rewriting -> Retrieve Work Orders -> Retrieve SOPs -> Synthesize
"""
import os
from typing import TypedDict, Annotated, Sequence
import operator
from langgraph.graph import StateGraph, END
from llama_index.llms.google_genai import GoogleGenAI
from llama_index.core import QueryBundle
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from dotenv import load_dotenv

load_dotenv()

from src.retriever import HybridGraphRetriever
from src.generator import generate_answer

# Define State
class RCAState(TypedDict):
    query: str
    original_query: str
    work_orders_context: list
    sops_context: list
    final_answer: str
    status: str

# Helper to initialize LLM and Retriever
def get_llm():
    return GoogleGenAI(model="gemini-2.5-flash-lite", api_key=os.getenv("GOOGLE_API_KEY"))

def get_retriever(collections: list[str]):
    embed_model = HuggingFaceEmbedding(model_name="BAAI/bge-small-en-v1.5")
    chroma_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "chroma_db"))
    return HybridGraphRetriever(
        chroma_db_path=chroma_path,
        collection_names=collections,
        embed_model=embed_model
    )

# --- Nodes ---

def rewrite_query(state: RCAState):
    """Day 7: Query Rewriting for informal language."""
    llm = get_llm()
    prompt = f"""Rewrite the following user query resolving any relative locations to explicit equipment tags using this list of known tags: [P-101, HV-204].
Original Query: {state['original_query']}
Rewritten Query:"""
    response = llm.complete(prompt)
    rewritten = str(response).strip()
    return {"query": rewritten, "status": f"Rewrote query to: {rewritten}"}

def retrieve_work_orders(state: RCAState):
    retriever = get_retriever(["work_orders"])
    nodes = retriever._retrieve(QueryBundle(state['query']))
    return {"work_orders_context": nodes, "status": "Searching past work orders..."}

def retrieve_sops(state: RCAState):
    retriever = get_retriever(["sops"])
    nodes = retriever._retrieve(QueryBundle(state['query']))
    return {"sops_context": nodes, "status": "Searching OEM manual / SOPs..."}

def synthesize(state: RCAState):
    llm = get_llm()
    all_nodes = state.get('work_orders_context', []) + state.get('sops_context', [])
    answer = generate_answer(state['query'], all_nodes, llm)
    return {"final_answer": answer, "status": "Synthesized final RCA."}


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
    from dotenv import load_dotenv
    load_dotenv()
    
    app = build_rca_graph()
    inputs = {"original_query": "failures related to that pump leaking", "query": ""}
    
    for output in app.stream(inputs):
        for key, value in output.items():
            print(f"[{key}] {value.get('status', '')}")
            if "final_answer" in value:
                print(f"\nFinal RCA:\n{value['final_answer']}")
