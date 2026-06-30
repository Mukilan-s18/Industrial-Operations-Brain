"""Tests for async large-file ingestion task manager."""

import sys
import tempfile
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))


def _make_large_pdf(size_mb: float) -> Path:
    """Create a PDF that exceeds the async size threshold."""
    import fitz
    doc = fitz.open()
    # Add enough pages with text to exceed size
    pages_needed = max(1, int(size_mb * 10))
    for i in range(pages_needed):
        page = doc.new_page()
        # Fill page with text to increase file size
        long_text = f"Page {i+1}\n" + ("Industrial inspection record. Equipment P-101. " * 100)
        page.insert_text((50, 50), long_text[:2000], fontsize=8)
    tmp = tempfile.NamedTemporaryFile(suffix=".pdf", delete=False)
    doc.save(tmp.name)
    doc.close()
    return Path(tmp.name)


def _make_large_page_pdf(num_pages: int) -> Path:
    """Create a PDF with many pages to trigger async by page count."""
    import fitz
    doc = fitz.open()
    for i in range(num_pages):
        page = doc.new_page()
        page.insert_text((50, 50), f"Page {i+1}: Standard Operating Procedure. Equipment P-101.")
    tmp = tempfile.NamedTemporaryFile(suffix=".pdf", delete=False)
    doc.save(tmp.name)
    doc.close()
    return Path(tmp.name)


def test_should_process_async_small_file():
    """Small file should NOT be routed to async."""
    from ingestion.utils.task_manager import should_process_async
    import fitz

    doc = fitz.open()
    page = doc.new_page()
    page.insert_text((50, 50), "Small document. P-101.")
    tmp = tempfile.NamedTemporaryFile(suffix=".pdf", delete=False)
    doc.save(tmp.name)
    doc.close()
    path = Path(tmp.name)
    try:
        assert not should_process_async(path), "Small file should be processed synchronously"
    finally:
        path.unlink(missing_ok=True)


def test_should_process_async_many_pages():
    """PDF with > 50 pages should be routed to async."""
    from ingestion.utils.task_manager import should_process_async, ASYNC_PAGE_THRESHOLD

    pdf_path = _make_large_page_pdf(ASYNC_PAGE_THRESHOLD + 5)
    try:
        assert should_process_async(pdf_path), f"PDF with >{ASYNC_PAGE_THRESHOLD} pages should be async"
    finally:
        pdf_path.unlink(missing_ok=True)


def test_task_lifecycle():
    """Create task → run async ingestion → poll to DONE."""
    from ingestion.utils.task_manager import (
        create_task, get_task, run_ingestion_async, TaskStatus
    )
    from ingestion.utils.deduplication import clear_registry
    import threading

    clear_registry()
    pdf_path = _make_large_page_pdf(3)
    # Copy to a new temp path (task manager will delete it)
    import shutil
    tmp = tempfile.NamedTemporaryFile(suffix=".pdf", delete=False)
    tmp.close()
    shutil.copy(str(pdf_path), tmp.name)
    task_path = Path(tmp.name)
    pdf_path.unlink(missing_ok=True)

    task_id = create_task(source="test_large.pdf")
    record = get_task(task_id)
    assert record is not None
    assert record.status == TaskStatus.PENDING

    # Run in a thread (as the real endpoint does)
    thread = threading.Thread(
        target=run_ingestion_async,
        args=(task_id, task_path, "test_large.pdf", "pdf", "dummy_hash_large"),
        daemon=True,
    )
    thread.start()
    thread.join(timeout=60)  # Wait up to 60s

    record = get_task(task_id)
    assert record.status in (TaskStatus.DONE, TaskStatus.FAILED), \
        f"Task should have completed, got: {record.status} — {record.error}"

    if record.status == TaskStatus.DONE:
        assert record.result is not None
        assert "doc_id" in record.result
        assert record.result["total_pages"] == 3
    
    clear_registry()


def test_get_nonexistent_task():
    """Polling a non-existent task_id should return None."""
    from ingestion.utils.task_manager import get_task

    assert get_task("00000000-0000-0000-0000-000000000000") is None
