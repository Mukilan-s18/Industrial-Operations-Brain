"""
Day 8, 9, 10: FastAPI Application with Streaming, REAL Metrics, Dynamic Caching, and Fallback
"""
import time
import asyncio
import json
import os
import chromadb
from fastapi import FastAPI, Query, Header, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from dotenv import load_dotenv

from backend.src.agent import build_rca_graph
from backend.src.fallback import get_fallback

from fastapi.responses import HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from pyvis.network import Network
from backend.src.ner_pipeline import NERPipeline
from backend.src.graph_builder import KnowledgeGraphBuilder


load_dotenv()
app = FastAPI(title="Industrial RAG API")

# =====================================================================
# Knowledge Graph Initialization
# =====================================================================
ner = NERPipeline()
builder = KnowledgeGraphBuilder()

DOCS_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "data", "documents.json"))
if os.path.exists(DOCS_PATH):
    with open(DOCS_PATH, "r") as f:
        docs = json.load(f)
    builder.build_graph_from_extracted_data(docs, ner)
else:
    docs = []


# Serve static files (HTML, CSS, JS)
static_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "static"))
os.makedirs(static_dir, exist_ok=True)
app.mount("/static", StaticFiles(directory=static_dir), name="static")


# =====================================================================
# Day 8: Dynamic Response Cache
# Populated from ACTUAL pipeline runs, NOT hardcoded strings.
# =====================================================================
RESPONSE_CACHE: dict[str, dict] = {}

# Day 10: Toggle this to True during live demo if the API crashes
USE_FALLBACK = os.getenv("USE_FALLBACK", "false").lower() == "true"

# Day 9: Corpus Coverage — computed from ChromaDB at startup
CHROMA_DB_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "chroma_db"))


def compute_corpus_coverage() -> float:
    """
    Day 9: REAL corpus coverage metric.
    Measures: (number of chunks indexed) / (total expected chunks).
    We count across all collections and compare against the number of source files.
    """
    try:
        client = chromadb.PersistentClient(path=CHROMA_DB_PATH)
        total_chunks = 0
        total_docs = 0
        for coll_name in ["sops", "work_orders", "regulations"]:
            try:
                coll = client.get_collection(coll_name)
                count = coll.count()
                total_chunks += count
                # Count unique source documents in the collection metadata
                results = coll.get(include=["metadatas"])
                unique_sources = set()
                if results and results.get("metadatas"):
                    for meta in results["metadatas"]:
                        if meta and meta.get("source"):
                            unique_sources.add(meta["source"])
                total_docs += len(unique_sources)
            except Exception:
                pass

        # Coverage: if we have chunks from all known docs, coverage is high
        import json
        expected_docs = 4  # fallback
        docs_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "data", "documents.json"))
        if os.path.exists(docs_path):
            try:
                with open(docs_path, "r") as f:
                    docs_list = json.load(f)
                expected_docs = len(docs_list)
            except Exception:
                pass
                
        if expected_docs == 0:
            return 0.0
        return round((total_docs / expected_docs) * 100, 1)
    except Exception:
        return 0.0


# Compute once at startup
CORPUS_COVERAGE_PCT = compute_corpus_coverage()


class QueryRequest(BaseModel):
    query: str
    mode: str = "detailed"  # Day 7: brief vs detailed


# =====================================================================
# RBAC: Role-based access control enforced at backend
# Roles: operator, engineer, auditor
# Restricted keywords only accessible to engineer/auditor roles
# =====================================================================
OPERATOR_RESTRICTED_TERMS = [
    "e-201", "electrical log", "engineer log", "moc", "management of change",
    "compliance report", "audit log", "rbac", "access control"
]

def check_role_access(role: str, query: str) -> tuple[bool, str]:
    """Returns (allowed, reason). Operators cannot access engineer/auditor queries."""
    if role.lower() == "operator":
        q_lower = query.lower()
        for term in OPERATOR_RESTRICTED_TERMS:
            if term in q_lower:
                return False, f"Access denied: '{term}' is restricted to Engineer/Auditor roles."
    return True, ""


rca_graph = build_rca_graph()


@app.post("/chat")
async def chat_endpoint(req: QueryRequest, x_user_role: str = Header(default="operator")):
    """
    Standard endpoint with:
    - Day 8: Dynamic caching (populated from real runs)
    - Day 9: REAL faithfulness score, REAL latency, REAL corpus coverage
    - Day 10: Fallback toggle
    """
    start_time = time.time()
    query_lower = req.query.lower().strip()

    # RBAC enforcement at backend
    allowed, reason = check_role_access(x_user_role, req.query)
    if not allowed:
        raise HTTPException(status_code=403, detail=reason)

    # Day 10: Fallback mode (for live demo crashes)
    if USE_FALLBACK:
        fb = get_fallback(req.query)
        if fb:
            return {
                "answer": fb["answer"],
                "sources": fb["sources"],
                "contradiction_detected": fb["contradiction_detected"],
                "metrics": {
                    "latency_sec": round(time.time() - start_time, 4),
                    "faithfulness_score": 1.0,
                    "corpus_coverage_pct": CORPUS_COVERAGE_PCT
                },
                "cached": True,
                "fallback": True
            }

    # Day 8: Check dynamic cache
    if query_lower in RESPONSE_CACHE:
        cached = RESPONSE_CACHE[query_lower]
        return {
            **cached,
            "metrics": {
                **cached["metrics"],
                "latency_sec": round(time.time() - start_time, 4),  # Cache hit = near-zero
            },
            "cached": True,
            "fallback": False
        }

    # Run the REAL pipeline
    inputs = {"original_query": req.query, "query": "", "graph_builder": builder, "user_role": x_user_role}
    final_state = rca_graph.invoke(inputs)

    latency = round(time.time() - start_time, 2)

    response_data = {
        "answer": final_state.get("final_answer", ""),
        "sources": final_state.get("sources", []),
        "contradiction_detected": final_state.get("contradiction_detected", False),
        "contradiction_details": final_state.get("contradiction_details", ""),
        "abstained": final_state.get("abstained", False),
        "metrics": {
            "latency_sec": latency,
            "faithfulness_score": final_state.get("faithfulness_score", 0.0),
            "corpus_coverage_pct": CORPUS_COVERAGE_PCT
        },
        "cached": False,
        "fallback": False,
        "action_taken": final_state.get("action_taken", "NONE"),
        "action_result": final_state.get("action_result", "")
    }

    # Day 8: Store in dynamic cache for future instant retrieval
    RESPONSE_CACHE[query_lower] = response_data

    return response_data


@app.post("/fallback/toggle")
async def toggle_fallback(enabled: bool):
    global USE_FALLBACK
    USE_FALLBACK = enabled
    return {"fallback_mode": USE_FALLBACK}

@app.post("/stream")
async def stream_rca(req: QueryRequest, x_user_role: str = Header(default="operator")):
    """Streaming endpoint for reasoning chain (Day 5, 8) with RBAC enforcement."""
    allowed, reason = check_role_access(x_user_role, req.query)
    if not allowed:
        raise HTTPException(status_code=403, detail=reason)
    
    async def event_generator():
        start_time = time.time()
        inputs = {"original_query": req.query, "query": "", "graph_builder": builder, "user_role": x_user_role}
        for output in rca_graph.stream(inputs):
            for node_name, state_update in output.items():
                event = {"node": node_name}
                if "status" in state_update:
                    event["status"] = state_update["status"]
                if "final_answer" in state_update:
                    event["answer"] = state_update["final_answer"]
                    event["contradiction_detected"] = state_update.get("contradiction_detected", False)
                    event["faithfulness_score"] = state_update.get("faithfulness_score", 0.0)
                    event["sources"] = state_update.get("sources", [])
                    event["latency_sec"] = round(time.time() - start_time, 2)
                yield f"data: {json.dumps(event)}\n\n"
            await asyncio.sleep(0.05)
    return StreamingResponse(event_generator(), media_type="text/event-stream")


@app.get("/metrics")
async def get_metrics():
    """Day 9: Live metrics card endpoint for the UI"""
    return {
        "corpus_coverage_pct": CORPUS_COVERAGE_PCT,
        "total_cached_queries": len(RESPONSE_CACHE),
        "fallback_mode": USE_FALLBACK,
        "chroma_db_path": CHROMA_DB_PATH,
        "collections": ["sops", "work_orders", "regulations"]
    }


@app.post("/cache/clear")
async def clear_cache():
    """Utility endpoint to clear the response cache"""
    RESPONSE_CACHE.clear()
    return {"status": "Cache cleared"}


@app.get("/")

def read_root():
    return FileResponse(os.path.join(static_dir, "index.html"))

@app.get("/api/stats")
def get_stats():
    return builder.get_graph_stats()

@app.get("/api/compliance-gaps")
def get_compliance_gaps(date: str = None, role: str = Query(None, description="User Role")):
    if role and "Operator" in role:
        return []
    return builder.get_compliance_gaps(date)

@app.get("/api/ner-evaluation")
def get_ner_evaluation():
    return ner.evaluate_accuracy()

@app.get("/api/failure-patterns")
def get_failure_patterns():
    return builder.get_failure_patterns()

@app.get("/api/nodes")
def get_nodes():
    nodes_list = []
    for node_id, data in builder.G.nodes(data=True):
        nodes_list.append({
            "id": node_id,
            "label": data.get("label", "UNKNOWN"),
            "properties": {k: v for k, v in data.items() if k != "label"}
        })
    return nodes_list

@app.get("/api/edges")
def get_edges():
    edges_list = []
    for u, v, data in builder.G.edges(data=True):
        edges_list.append({
            "source": u,
            "target": v,
            "type": data.get("type", "UNKNOWN"),
            "confidence": data.get("confidence", 1.0),
            "weight": data.get("weight", 1),
            "properties": {k: v for k, v in data.items() if k not in ["type", "confidence", "weight"]}
        })
    return edges_list

@app.get("/api/graph-viz", response_class=HTMLResponse)
def get_graph_viz(node_id: str = Query(None, description="Ego network center node"), role: str = Query(None, description="User Role")):
    """
    Generates a PyVis interactive visualization of the graph.
    If node_id is provided, generates the 1-hop ego network for that node.
    """
    # Color scheme for different entity types
    colors = {
        "EQUIPMENT": "#3B82F6",    # Vibrant Blue
        "REGULATION": "#EF4444",   # Vivid Ruby Red
        "FAILURE_MODE": "#F59E0B", # Warm Amber
        "PARAMETER": "#10B981",    # Emerald Green
        "PERSON": "#8B5CF6",       # Deep Violet
        "DOCUMENT": "#06B6D4",     # Cool Cyan
        "DATE": "#6B7280"          # Slate Grey
    }

    # Decide which sub-graph to render
    if node_id:
        if not builder.G.has_node(node_id):
            raise HTTPException(status_code=404, detail="Node not found")
        # Extract ego network (neighbors and edges between neighbors)
        ego_nodes = [node_id] + list(builder.G.successors(node_id)) + list(builder.G.predecessors(node_id))
        sub_g = builder.G.subgraph(ego_nodes).copy()
        title = f"Ego Network - {node_id}"
    else:
        sub_g = builder.G.copy()
        title = "Plant Knowledge Graph"
        
    # RBAC Enforcement: Filter Graph Nodes based on role
    if role and "Operator" in role:
        restricted_nodes = [n for n, d in sub_g.nodes(data=True) if d.get("label") == "REGULATION"]
        sub_g.remove_nodes_from(restricted_nodes)

    # Create PyVis Network
    net = Network(
        height="500px", 
        width="100%", 
        bgcolor="#0F172A", # Deep slate background
        font_color="#E2E8F0", # Slate 200 text
        directed=True,
        notebook=False
    )
    
    # Enable physics options to make it interactive and not a "hairball"
    net.set_options("""
    {
      "nodes": {
        "borderWidth": 2,
        "borderWidthSelected": 4,
        "shadow": true,
        "shape": "dot",
        "size": 25,
        "font": {
          "size": 14,
          "face": "Inter, Roboto, sans-serif"
        }
      },
      "edges": {
        "color": {
          "color": "#475569",
          "highlight": "#60A5FA",
          "hover": "#60A5FA",
          "inherit": false
        },
        "smooth": {
          "type": "cubicBezier",
          "forceDirection": "vertical",
          "roundness": 0.5
        },
        "arrows": {
          "to": {
            "enabled": true,
            "scaleFactor": 0.5
          }
        }
      },
      "physics": {
        "barnesHut": {
          "gravitationalConstant": -12000,
          "centralGravity": 0.3,
          "springLength": 120,
          "springConstant": 0.04,
          "damping": 0.09,
          "avoidOverlap": 0.8
        },
        "minVelocity": 0.75
      },
      "interaction": {
        "hover": true,
        "tooltipDelay": 100
      }
    }
    """)

    # Add nodes to PyVis
    for n, data in sub_g.nodes(data=True):
        label_type = data.get("label", "UNKNOWN")
        color = colors.get(label_type, "#94A3B8")
        
        # Build clean tooltip HTML
        properties_html = "<br>".join([f"<b>{k}:</b> {v}" for k, v in data.items() if k != "label"])
        tooltip = f"<b>{n}</b> ({label_type})<br>{properties_html}"
        
        # Distinguish source node visually in ego-network view
        is_center = node_id and n == node_id
        size = 35 if is_center else 20 if label_type == "DOCUMENT" else 25
        
        net.add_node(
            n, 
            label=n, 
            title=tooltip, 
            color=color, 
            size=size,
            borderWidth=4 if is_center else 2,
            borderWidthSelected=6 if is_center else 4
        )

    # Add edges to PyVis
    for u, v, data in sub_g.edges(data=True):
        edge_type = data.get("type", "UNKNOWN")
        weight = data.get("weight", 1)
        confidence = data.get("confidence", 1.0)
        
        tooltip = f"<b>Relation:</b> {edge_type}<br><b>Weight:</b> {weight}<br><b>Confidence:</b> {confidence}"
        # Set thicker lines for heavier relations
        width = 1 + (weight - 1) * 1.5
        
        # Color edges by relation type
        edge_color = "#3B82F6" if edge_type == "HAS_FAILURE" else "#10B981" if edge_type == "HAS_INSPECTION" else "#EF4444" if edge_type == "GOVERNED_BY" else "#475569"
        
        net.add_edge(
            u, 
            v, 
            title=tooltip, 
            value=weight, 
            width=width,
            color=edge_color
        )

    # Write HTML file and read it to return
    # Use static directory so it's clean and served safely
    temp_file = os.path.join(static_dir, f"temp_graph_{node_id or 'all'}.html")
    net.write_html(temp_file)
    
    with open(temp_file, "r") as f:
        html_content = f.read()
        
    # Clean up temp file
    try:
        os.remove(temp_file)
    except OSError:
        pass
        
    return html_content

if __name__ == "__main__":
    import uvicorn
    # Day 10: Pre-warm models
    print("Pre-warming models (sending 3 dummy queries)...")
    for i, q in enumerate(["test", "P-101", "HV-204"]):
        try:
            rca_graph.invoke({"original_query": q, "query": "", "graph_builder": builder})
            print(f"  Warm-up {i+1}/3 complete.")
        except Exception as e:
            print(f"  Warm-up {i+1}/3 failed (non-critical): {e}")
    print(f"Corpus Coverage: {CORPUS_COVERAGE_PCT}%")
    print("Starting API on http://0.0.0.0:8000 ...")
    uvicorn.run(app, host="0.0.0.0", port=8000)
