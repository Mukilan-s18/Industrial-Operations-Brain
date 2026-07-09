"""
Async Task Manager: Handles background ingestion for large files.
Files > 5MB or > 50 pages are processed asynchronously.
Returns a task_id immediately; poll /ingest/status/{task_id} for results.
"""

import logging
import threading
import time
import uuid
from enum import Enum
from pathlib import Path
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)

# Thresholds for async processing
ASYNC_FILE_SIZE_BYTES = 5 * 1024 * 1024  # 5 MB
ASYNC_PAGE_THRESHOLD = 50


class TaskStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    DONE = "done"
    FAILED = "failed"


class TaskRecord:
    def __init__(self, task_id: str, source: str):
        self.task_id = task_id
        self.source = source
        self.status = TaskStatus.PENDING
        self.result: Optional[Any] = None
        self.error: Optional[str] = None
        self.created_at = time.time()
        self.completed_at: Optional[float] = None
        self.progress: str = "Queued"


# In-memory task registry
_tasks: Dict[str, TaskRecord] = {}
_lock = threading.Lock()


def _evict_old_tasks():
    """Evict DONE or FAILED tasks older than 1 hour (3600 seconds)."""
    now = time.time()
    to_delete = []
    with _lock:
        for task_id, record in _tasks.items():
            if (
                record.status in (TaskStatus.DONE, TaskStatus.FAILED)
                and record.completed_at
            ):
                if now - record.completed_at > 3600:
                    to_delete.append(task_id)
        for task_id in to_delete:
            del _tasks[task_id]


def create_task(source: str) -> str:
    """Create a new async task and return its task_id."""
    _evict_old_tasks()
    task_id = str(uuid.uuid4())
    record = TaskRecord(task_id=task_id, source=source)
    with _lock:
        _tasks[task_id] = record
    logger.info(f"Task created: {task_id} for '{source}'")
    return task_id


def get_task(task_id: str) -> Optional[TaskRecord]:
    """Retrieve a task record by ID."""
    _evict_old_tasks()
    with _lock:
        return _tasks.get(task_id)


def run_ingestion_async(
    task_id: str, tmp_path: Path, filename: str, category: str, file_hash: str
):
    """
    Run full ingestion in a background thread.
    Updates the TaskRecord in-place as processing proceeds.
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

    record = get_task(task_id)
    if not record:
        return

    with _lock:
        record.status = TaskStatus.RUNNING
        record.progress = "Processing started"

    start_time = time.perf_counter()
    warnings = []

    try:
        with _lock:
            record.progress = f"Extracting {category}..."

        pages, doc_type, pipe_warnings = run_extraction_pipeline(tmp_path, category)
        warnings.extend(pipe_warnings)

        with _lock:
            record.progress = "Extracting metadata..."

        first_pages_text = " ".join(p.text for p in pages[:3])
        full_text = " ".join(p.text for p in pages)

        metadata = DocumentMetadata(
            rev_number=extract_revision(first_pages_text),
            date=extract_date(first_pages_text),
            equipment_ids=extract_equipment_ids(full_text),
            language=detect_language(full_text)[0],
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

        with _lock:
            record.status = TaskStatus.DONE
            record.result = result.model_dump()
            record.completed_at = time.time()
            record.progress = (
                f"Done — {len(pages)} pages processed in {elapsed_ms:.0f}ms"
            )

        logger.info(f"Task {task_id} completed: {filename} ({elapsed_ms:.0f}ms)")

    except Exception as e:
        logger.error(f"Task {task_id} failed: {e}")
        with _lock:
            record.status = TaskStatus.FAILED
            record.error = str(e)
            record.completed_at = time.time()
            record.progress = f"Failed: {e}"
    finally:
        try:
            tmp_path.unlink(missing_ok=True)
        except Exception:
            pass


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
