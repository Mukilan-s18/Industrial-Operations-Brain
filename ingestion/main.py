"""
Main FastAPI application entry point.
Wires up all routers, configures logging, and sets up CORS.
"""

import logging
import sys
import time
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

from ingestion.health import router as health_router
from ingestion.routers.ingest import router as ingest_router

# ── Logging Configuration ─────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("ingestion.log", encoding="utf-8"),
    ],
)
logger = logging.getLogger("ingestion.main")


# ── Lifespan (startup/shutdown) ───────────────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("=" * 60)
    logger.info("🏭  Industrial Operations Brain — Ingestion Service")
    logger.info("=" * 60)
    logger.info("Service starting up...")
    yield
    logger.info("Service shutting down.")


# ── App ───────────────────────────────────────────────────────────────────────
app = FastAPI(
    title="Industrial Operations Brain — Ingestion API",
    description=(
        "Multi-format document ingestion pipeline for industrial operations. "
        "Processes PDFs, scanned documents, spreadsheets, and work orders into "
        "structured JSON for RAG and knowledge graph consumption."
    ),
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# ── CORS ──────────────────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:8501"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Logging Middleware ────────────────────────────────────────────────────────
@app.middleware("http")
async def log_requests(request: Request, call_next):
    start = time.perf_counter()
    response = await call_next(request)
    elapsed_ms = (time.perf_counter() - start) * 1000
    logger.info(
        f"{request.method} {request.url.path} → {response.status_code} "
        f"({elapsed_ms:.1f}ms)"
    )
    return response


# ── Routers ───────────────────────────────────────────────────────────────────
app.include_router(ingest_router)
app.include_router(health_router)


# ── Root ──────────────────────────────────────────────────────────────────────
@app.get("/", include_in_schema=False)
async def root():
    return {
        "service": "Industrial Operations Brain — Ingestion API",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health",
        "ingest": "POST /ingest/",
    }


# ── Entry Point ───────────────────────────────────────────────────────────────
if __name__ == "__main__":
    uvicorn.run("ingestion.main:app", host="0.0.0.0", port=8000, reload=True)
