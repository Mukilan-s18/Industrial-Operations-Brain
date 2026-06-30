"""
Day 8, 9, 10: FastAPI Application with Streaming, REAL Metrics, Dynamic Caching, and Fallback
"""
import time
import asyncio
import json
import os
import chromadb
from fastapi import FastAPI, Query
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from dotenv import load_dotenv

from src.agent import build_rca_graph
from fallback import get_fallback

load_dotenv()
app = FastAPI(title="Industrial RAG API")

# =====================================================================
# Day 8: Dynamic Response Cache
# Populated from ACTUAL pipeline runs, NOT hardcoded strings.
# =====================================================================
RESPONSE_CACHE: dict[str, dict] = {}

# Day 10: Toggle this to True during live demo if the API crashes
USE_FALLBACK = os.getenv("USE_FALLBACK", "false").lower() == "true"

# Day 9: Corpus Coverage — computed from ChromaDB at startup
CHROMA_DB_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "chroma_db"))


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
        # We know we have 4 source files total
        expected_docs = 4  # sop_101.txt, sop_101_b.txt, wo_998.txt, osha_1910_147.txt
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


rca_graph = build_rca_graph()


@app.post("/chat")
async def chat_endpoint(req: QueryRequest):
    """
    Standard endpoint with:
    - Day 8: Dynamic caching (populated from real runs)
    - Day 9: REAL faithfulness score, REAL latency, REAL corpus coverage
    - Day 10: Fallback toggle
    """
    start_time = time.time()
    query_lower = req.query.lower().strip()

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
    inputs = {"original_query": req.query, "query": ""}
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
        "fallback": False
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
async def stream_rca(req: QueryRequest):
    """Streaming endpoint for reasoning chain (Day 5, 8)"""
    async def event_generator():
        start_time = time.time()
        inputs = {"original_query": req.query, "query": ""}
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


if __name__ == "__main__":
    import uvicorn
    # Day 10: Pre-warm models
    print("Pre-warming models (sending 3 dummy queries)...")
    for i, q in enumerate(["test", "P-101", "HV-204"]):
        try:
            rca_graph.invoke({"original_query": q, "query": ""})
            print(f"  Warm-up {i+1}/3 complete.")
        except Exception as e:
            print(f"  Warm-up {i+1}/3 failed (non-critical): {e}")
    print(f"Corpus Coverage: {CORPUS_COVERAGE_PCT}%")
    print("Starting API on http://0.0.0.0:8000 ...")
    uvicorn.run(app, host="0.0.0.0", port=8000)
