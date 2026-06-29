"""
Health endpoint: checks Tesseract, disk space, and service readiness.
"""

import logging
import shutil
import subprocess
from pathlib import Path

from fastapi import APIRouter
from fastapi.responses import JSONResponse

from ingestion.models.schemas import HealthStatus
from ingestion.utils.deduplication import get_registry_size

logger = logging.getLogger(__name__)
router = APIRouter(tags=["health"])

MIN_FREE_DISK_GB = 1.0  # Require at least 1 GB free


def _check_tesseract() -> bool:
    """Check if Tesseract is on PATH and executable."""
    try:
        result = subprocess.run(
            ["tesseract", "--version"],
            capture_output=True, text=True, timeout=5
        )
        return result.returncode == 0
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return False


def _check_disk_space() -> tuple[bool, float]:
    """Check free disk space at the working directory."""
    try:
        usage = shutil.disk_usage(Path.cwd())
        free_gb = usage.free / (1024 ** 3)
        return free_gb >= MIN_FREE_DISK_GB, free_gb
    except Exception:
        return False, 0.0


@router.get("/health", response_model=HealthStatus, summary="Service health check")
async def health_check() -> HealthStatus:
    """
    Check that all services are available:
    - Tesseract OCR is on PATH
    - Sufficient disk space
    - Ingestion registry status
    """
    tesseract_ok = _check_tesseract()
    disk_ok, free_gb = _check_disk_space()

    overall = "ok"
    if not tesseract_ok or not disk_ok:
        overall = "degraded"

    status = HealthStatus(
        status=overall,
        tesseract_available=tesseract_ok,
        disk_space_ok=disk_ok,
        services={
            "free_disk_gb": round(free_gb, 2),
            "documents_indexed": get_registry_size(),
            "tesseract": "available" if tesseract_ok else "NOT FOUND — OCR disabled",
            "api": "running",
        },
    )

    http_code = 200 if overall == "ok" else 207
    return JSONResponse(content=status.model_dump(), status_code=http_code)
