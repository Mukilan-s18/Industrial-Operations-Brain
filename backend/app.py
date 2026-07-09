"""
Day 8, 9, 10: FastAPI Application with Streaming, REAL Metrics, Dynamic Caching, and Fallback
Refactored into modular routers.
"""

import os
import structlog
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.sdk.resources import Resource
from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from backend.settings import settings
from backend.dependencies import CORPUS_COVERAGE_PCT, rca_graph, builder
from backend.routers import chat, graph, compliance, auth

try:
    import phoenix as px
    from llama_index.core import set_global_handler

    # Enable Arize Phoenix tracing for LlamaIndex
    set_global_handler("arize_phoenix")
except ImportError as e:
    import logging

    logging.warning(f"Could not load Arize Phoenix (observability disabled): {e}")

from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware

# Setup Structlog
structlog.configure(
    processors=[
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.stdlib.add_log_level,
        structlog.processors.JSONRenderer(),
    ]
)
logger = structlog.get_logger(__name__)

# Setup OpenTelemetry
resource = Resource(attributes={"service.name": "industrial-copilot-backend"})
provider = TracerProvider(resource=resource)
processor = BatchSpanProcessor(OTLPSpanExporter())
provider.add_span_processor(processor)
trace.set_tracer_provider(provider)

from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="Industrial RAG API")

# Setup Rate Limiting
app.state.limiter = chat.limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_middleware(SlowAPIMiddleware)

# Instrument FastAPI with OpenTelemetry
FastAPIInstrumentor.instrument_app(app)

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
app.include_router(auth.router)
app.include_router(chat.router)
app.include_router(graph.router)
app.include_router(compliance.router)


@app.get("/metrics")
async def get_metrics():
    """Live metrics card endpoint for the UI"""
    return {
        "corpus_coverage_pct": CORPUS_COVERAGE_PCT,
        "total_cached_queries": -1,  # Disabled as we moved to Redis
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
