"""
Async Task Manager: Handles background ingestion for large files via Celery.
Files > 5MB or > 50 pages are processed asynchronously.
Returns a task_id immediately; poll /ingest/status/{task_id} for results.
"""

import logging
import time
from enum import Enum
from pathlib import Path
from backend.celery_app import celery_app

logger = logging.getLogger(__name__)

# Thresholds for async processing
ASYNC_FILE_SIZE_BYTES = 5 * 1024 * 1024  # 5 MB
ASYNC_PAGE_THRESHOLD = 50


class TaskStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    DONE = "done"
    FAILED = "failed"


@celery_app.task(bind=True, name="run_ingestion_async")
def run_ingestion_async(
    self, tmp_path_str: str, filename: str, category: str, file_hash: str
):
    """
    Run full ingestion in a Celery background task.
    Updates the task state in-place as processing proceeds.
    """
    from ingestion.utils.pipeline import run_extraction_pipeline
    from ingestion.utils.deduplication import register_document
    from ingestion.utils.language import detect_language
    from ingestion.utils.metadata import (
        extract_date,
        extract_equipment_ids,
        extract_revision,
    )
    from ingestion.models.schemas import (
        DocumentMetadata,
        IngestionResult,
    )

    tmp_path = Path(tmp_path_str)
    start_time = time.perf_counter()
    warnings = []

    try:
        self.update_state(
            state="RUNNING", meta={"progress": f"Extracting {category}..."}
        )

        pages, doc_type, pipe_warnings = run_extraction_pipeline(tmp_path, category)
        warnings.extend(pipe_warnings)

        self.update_state(state="RUNNING", meta={"progress": "Extracting metadata..."})

        first_pages_text = " ".join(p.text for p in pages[:3])
        full_text = " ".join(p.text for p in pages)

        metadata = DocumentMetadata(
            rev_number=extract_revision(first_pages_text),
            date=extract_date(first_pages_text),
            equipment_ids=extract_equipment_ids(full_text),
            language=detect_language(full_text)[0] if full_text else "en",
            requires_manual_review=any(getattr(p, "error", None) for p in pages),
        )

        elapsed_ms = (time.perf_counter() - start_time) * 1000
        result = IngestionResult(
            doc_id=file_hash,
            source=filename,
            doc_type=doc_type,
            pages=pages,
            metadata=metadata,
            total_pages=len(pages),
            processing_time_ms=round(elapsed_ms, 2),
            warnings=warnings,
        )
        register_document(file_hash, file_hash, filename)

        logger.info(f"Task completed: {filename} ({elapsed_ms:.0f}ms)")

        # Return the actual result dict to store in Redis
        return {
            "result": result.model_dump(),
            "progress": f"Done — {len(pages)} pages processed in {elapsed_ms:.0f}ms",
            "source": filename,
        }

    except Exception as e:
        logger.error(f"Task failed: {e}")
        # Raising an exception will make the task FAILED in celery
        raise e
    finally:
        try:
            if tmp_path.exists():
                tmp_path.unlink(missing_ok=True)
        except Exception:
            pass


def get_task_status(task_id: str) -> dict:
    from celery.result import AsyncResult

    res = AsyncResult(task_id, app=celery_app)

    status = TaskStatus.PENDING
    progress = "Queued"
    result = None
    error = None

    if res.state == "PENDING":
        status = TaskStatus.PENDING
    elif res.state in ("STARTED", "RUNNING"):
        status = TaskStatus.RUNNING
        if isinstance(res.info, dict):
            progress = res.info.get("progress", progress)
    elif res.state == "SUCCESS":
        status = TaskStatus.DONE
        if isinstance(res.info, dict):
            result = res.info.get("result")
            progress = res.info.get("progress", "Done")
    elif res.state == "FAILURE":
        status = TaskStatus.FAILED
        error = str(res.info)
        progress = f"Failed: {error}"

    return {
        "task_id": task_id,
        "status": status,
        "progress": progress,
        "result": result,
        "error": error,
    }


def should_process_async(file_path: Path) -> bool:
    """Return True if the file should be processed asynchronously."""
    size = file_path.stat().st_size
    if size > ASYNC_FILE_SIZE_BYTES:
        logger.info(
            f"File {file_path.name} is {size / 1024 / 1024:.1f}MB — routing to async"
        )
        return True

    # Quick page count check for PDFs
    if file_path.suffix.lower() == ".pdf":
        try:
            import fitz

            doc = fitz.open(str(file_path))
            pages = len(doc)
            doc.close()
            if pages > ASYNC_PAGE_THRESHOLD:
                logger.info(
                    f"File {file_path.name} has {pages} pages — routing to async"
                )
                return True
        except Exception:
            pass

    return False
