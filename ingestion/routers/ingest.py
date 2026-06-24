"""
/ingest router: FastAPI endpoint for document ingestion.
Handles PDF, Excel, and CSV/work-order files.
Large files (>5MB or >50 pages) are processed asynchronously.
"""

import json
import logging
import tempfile
import threading
import time
from pathlib import Path

from fastapi import APIRouter, File, HTTPException, UploadFile
from fastapi.responses import JSONResponse

from ingestion.models.schemas import (
    DocType,
    DocumentMetadata,
    IngestionResult,
    PageResult,
)
from ingestion.processors.excel_processor import extract_excel
from ingestion.processors.pdf_processor import extract_pdf
from ingestion.processors.workorder_processor import extract_work_orders
from ingestion.utils.deduplication import (
    check_duplicate,
    register_document,
)
from ingestion.utils.language import detect_language
from ingestion.utils.metadata import (
    compute_file_hash,
    extract_date,
    extract_equipment_ids,
    extract_revision,
    normalize_document_title,
)
from ingestion.utils.task_manager import (
    TaskStatus,
    create_task,
    get_task,
    run_ingestion_async,
    should_process_async,
)
from ingestion.utils.validation import get_file_category, validate_file

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/ingest", tags=["ingestion"])

# In-process version registry for conflict detection: title → (doc_id, rev_number)
_version_registry: dict = {}


# ─────────────────────────────────────────────────────────────────────────────
# POST /ingest/
# ─────────────────────────────────────────────────────────────────────────────
@router.post("/", summary="Ingest a document (async for large files)")
async def ingest_document(file: UploadFile = File(...)):
    """
    Ingest a PDF, Excel, or CSV file.

    - **Small files** (<5MB, <50 pages): processed synchronously, returns `IngestionResult`.
    - **Large files** (≥5MB or ≥50 pages): processed in background, returns `{task_id, status}`.
      Poll `GET /ingest/status/{task_id}` for the result.
    """
    start_time = time.perf_counter()
    warnings = []

    # ── 1. Save to temp file ──────────────────────────────────────────────────
    suffix = Path(file.filename).suffix.lower() if file.filename else ".bin"
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        content = await file.read()
        tmp.write(content)
        tmp_path = Path(tmp.name)

    try:
        # ── 2. Validate ───────────────────────────────────────────────────────
        is_valid, error_msg = validate_file(tmp_path)
        if not is_valid:
            raise HTTPException(status_code=400, detail=error_msg)

        category = get_file_category(tmp_path)

        # ── 3. Deduplication check ────────────────────────────────────────────
        is_dup, file_hash, existing_id = check_duplicate(tmp_path)
        if is_dup:
            raise HTTPException(
                status_code=409,
                detail={
                    "message": "Duplicate document — already ingested",
                    "existing_doc_id": existing_id,
                    "file_hash": file_hash,
                },
            )

        # ── 4. Large file → async ─────────────────────────────────────────────
        if should_process_async(tmp_path):
            task_id = create_task(source=file.filename or "unknown")
            # Hand off tmp_path ownership to the background thread
            thread = threading.Thread(
                target=run_ingestion_async,
                args=(task_id, tmp_path, file.filename or "unknown", category),
                daemon=True,
            )
            thread.start()
            # tmp_path will be cleaned up by run_ingestion_async
            return JSONResponse(
                status_code=202,
                content={
                    "message": "Large file accepted for background processing",
                    "task_id": task_id,
                    "status": TaskStatus.PENDING,
                    "poll_url": f"/ingest/status/{task_id}",
                },
            )

        # ── 5. Small file → synchronous extraction ────────────────────────────
        if category == "pdf":
            pages, doc_type = extract_pdf(tmp_path)
        elif category == "excel":
            pages = extract_excel(tmp_path)
            doc_type = DocType.TABLE_HEAVY
        elif category == "csv":
            records = extract_work_orders(tmp_path)
            text = json.dumps(records, indent=2, default=str)
            pages = [PageResult(page=1, text=text, is_ocr=False)]
            doc_type = DocType.TABLE_HEAVY
            if any(r["requires_manual_review"] for r in records):
                warnings.append("Some work order records missing equipment_id — require manual review.")
        else:
            raise HTTPException(status_code=400, detail=f"Unsupported file category: {category}")

        # ── 6. Metadata extraction ────────────────────────────────────────────
        first_pages_text = " ".join(p.text for p in pages[:3])
        full_text = " ".join(p.text for p in pages)

        rev_number = extract_revision(first_pages_text)
        date = extract_date(first_pages_text)
        equipment_ids = extract_equipment_ids(full_text)
        lang, _ = detect_language(full_text)

        # ── 7. Version conflict detection ─────────────────────────────────────
        norm_title = normalize_document_title(file.filename or "")
        superseded_by = None
        has_conflict = False

        if norm_title in _version_registry:
            existing_doc_id, existing_rev = _version_registry[norm_title]
            if existing_rev and rev_number and rev_number != existing_rev:
                has_conflict = True
                try:
                    if float(rev_number) > float(existing_rev):
                        warnings.append(
                            f"Version conflict: this document (Rev {rev_number}) supersedes "
                            f"existing doc_id={existing_doc_id} (Rev {existing_rev})."
                        )
                    else:
                        superseded_by = existing_doc_id
                        warnings.append(
                            f"Version conflict: this document (Rev {rev_number}) is superseded by "
                            f"existing doc_id={existing_doc_id} (Rev {existing_rev})."
                        )
                except ValueError:
                    has_conflict = True

        _version_registry[norm_title] = (file_hash, rev_number)

        # ── 8. Build and return result ────────────────────────────────────────
        metadata = DocumentMetadata(
            rev_number=rev_number,
            date=date,
            superseded_by=superseded_by,
            equipment_ids=equipment_ids,
            language=lang,
            requires_manual_review=any(getattr(p, "error", None) for p in pages),
            has_version_conflict=has_conflict,
        )

        elapsed_ms = (time.perf_counter() - start_time) * 1000
        result = IngestionResult(
            doc_id=file_hash,
            source=file.filename or "unknown",
            doc_type=doc_type,
            pages=pages,
            metadata=metadata,
            total_pages=len(pages),
            processing_time_ms=round(elapsed_ms, 2),
            warnings=warnings,
        )

        register_document(file_hash, file_hash, file.filename or "unknown")
        logger.info(
            f"Ingested: {file.filename} | type={doc_type} | pages={len(pages)} | {elapsed_ms:.0f}ms"
        )
        return result

    finally:
        # Only clean up temp file for sync path — async path handles its own cleanup
        try:
            if tmp_path.exists():
                tmp_path.unlink(missing_ok=True)
        except Exception:
            pass


# ─────────────────────────────────────────────────────────────────────────────
# GET /ingest/status/{task_id}
# ─────────────────────────────────────────────────────────────────────────────
@router.get("/status/{task_id}", summary="Poll async ingestion task status")
async def get_ingestion_status(task_id: str):
    """
    Poll the status of a large-file background ingestion task.

    Returns:
    - `status: pending | running | done | failed`
    - `result`: full IngestionResult JSON when status is `done`
    - `error`: error message when status is `failed`
    """
    record = get_task(task_id)
    if not record:
        raise HTTPException(status_code=404, detail=f"Task '{task_id}' not found")

    response = {
        "task_id": task_id,
        "source": record.source,
        "status": record.status,
        "progress": record.progress,
        "created_at": record.created_at,
        "completed_at": record.completed_at,
    }

    if record.status == TaskStatus.DONE:
        response["result"] = record.result
    elif record.status == TaskStatus.FAILED:
        response["error"] = record.error

    return JSONResponse(content=response)
