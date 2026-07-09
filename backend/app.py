"""
Day 8, 9, 10: FastAPI Application with Streaming, REAL Metrics, Dynamic Caching, and Fallback
Refactored into modular routers.
"""

import os
import logging
from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from backend.settings import settings
from backend.dependencies import CORPUS_COVERAGE_PCT, rca_graph, builder
from backend.routers import chat, graph, compliance
from backend.routers.chat import RESPONSE_CACHE

logger = logging.getLogger(__name__)

from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="Industrial RAG API")

# Add CORS Middleware to allow Next.js (port 3000) to communicate
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins for local dev
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve static files (HTML, CSS, JS)
static_dir = settings.static_dir
os.makedirs(static_dir, exist_ok=True)
app.mount("/static", StaticFiles(directory=static_dir), name="static")

# Include Routers
app.include_router(chat.router)
app.include_router(graph.router)
app.include_router(compliance.router)


@app.get("/metrics")
async def get_metrics():
    """Live metrics card endpoint for the UI"""
    return {
        "corpus_coverage_pct": CORPUS_COVERAGE_PCT,
        "total_cached_queries": len(RESPONSE_CACHE),
        "fallback_mode": settings.use_fallback,
        "chroma_db_path": settings.chroma_db_path,
        "collections": ["sops", "work_orders", "regulations"],
    }


@app.get("/")
def read_root():
    return {"status": "API Online"}


if __name__ == "__main__":
    import uvicorn

    # Pre-warm models
    print("Pre-warming models (sending 3 dummy queries)...")
    config = {"configurable": {"thread_id": "warmup"}}
    for i, q in enumerate(["test", "P-101", "HV-204"]):
        try:
            rca_graph.invoke(
                {"original_query": q, "query": "", "graph_builder": builder},
                config=config,
            )
            print(f"  Warm-up {i + 1}/3 complete.")
        except Exception as e:
            print(f"  Warm-up {i + 1}/3 failed (non-critical): {e}")
    print(f"Corpus Coverage: {CORPUS_COVERAGE_PCT}%")
    print("Starting API on http://0.0.0.0:8000 ...")
    uvicorn.run(app, host="0.0.0.0", port=8000)
