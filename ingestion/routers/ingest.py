"""
/ingest router: FastAPI endpoint for document ingestion.
Handles PDF, Excel, and CSV/work-order files.
"""

import logging
import tempfile
import time
from pathlib import Path

from fastapi import APIRouter, File, HTTPException, UploadFile
from fastapi.responses import JSONResponse

from ingestion.models.schemas import (
    DocType,
    DocumentMetadata,
    IngestionError,
    IngestionResult,
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
    extract_date,
    extract_equipment_ids,
    extract_revision,
    normalize_document_title,
)
from ingestion.utils.validation import get_file_category, validate_file

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/ingest", tags=["ingestion"])

# In-process version registry for conflict detection: title → (doc_id, rev_number)
_version_registry: dict = {}


@router.post("/", response_model=IngestionResult, summary="Ingest a document")
async def ingest_document(file: UploadFile = File(...)) -> IngestionResult:
    """
    Ingest a PDF, Excel, or CSV file.

    Returns structured JSON with extracted text, tables, and metadata
    ready for RAG/knowledge-graph consumption.
    """
    start_time = time.perf_counter()
    warnings = []

    # ── 1. Save to temp file ─────────────────────────────────────────────────
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
            warnings.append(f"Duplicate file — already ingested as doc_id={existing_id}. Skipping.")
            raise HTTPException(
                status_code=409,
                detail={
                    "message": "Duplicate document — already ingested",
                    "existing_doc_id": existing_id,
                    "file_hash": file_hash,
                },
            )

        # ── 4. Extract content ────────────────────────────────────────────────
        if category == "pdf":
            pages, doc_type = extract_pdf(tmp_path)
        elif category == "excel":
            pages = extract_excel(tmp_path)
            doc_type = DocType.TABLE_HEAVY
        elif category == "csv":
            # Work orders — parse separately and build a single-page result
            records = extract_work_orders(tmp_path)
            import json
            from ingestion.models.schemas import ExtractedTable, PageResult
            text = json.dumps(records, indent=2, default=str)
            pages = [PageResult(page=1, text=text, is_ocr=False)]
            doc_type = DocType.TABLE_HEAVY
            if any(r["requires_manual_review"] for r in records):
                warnings.append("Some work order records are missing equipment_id and require manual review.")
        else:
            raise HTTPException(status_code=400, detail=f"Unsupported file category: {category}")

        # ── 5. Aggregate text for metadata extraction ─────────────────────────
        # Use only first 3 pages (as per plan)
        first_pages_text = " ".join(p.text for p in pages[:3])
        full_text = " ".join(p.text for p in pages)

        rev_number = extract_revision(first_pages_text)
        date = extract_date(first_pages_text)
        equipment_ids = extract_equipment_ids(full_text)
        lang, _ = detect_language(full_text)

        # ── 6. Version conflict detection ─────────────────────────────────────
        norm_title = normalize_document_title(file.filename or "")
        superseded_by = None
        has_conflict = False

        if norm_title in _version_registry:
            existing_doc_id, existing_rev = _version_registry[norm_title]
            if existing_rev and rev_number and rev_number != existing_rev:
                has_conflict = True
                try:
                    if float(rev_number) > float(existing_rev):
                        # This is the newer doc → old one is superseded
                        warnings.append(
                            f"Version conflict: this document (Rev {rev_number}) supersedes "
                            f"existing doc_id={existing_doc_id} (Rev {existing_rev})."
                        )
                    else:
                        # This is older → flag it as superseded
                        superseded_by = existing_doc_id
                        warnings.append(
                            f"Version conflict: this document (Rev {rev_number}) is superseded by "
                            f"existing doc_id={existing_doc_id} (Rev {existing_rev})."
                        )
                except ValueError:
                    has_conflict = True

        _version_registry[norm_title] = (file_hash, rev_number)

        # ── 7. Build output ───────────────────────────────────────────────────
        metadata = DocumentMetadata(
            rev_number=rev_number,
            date=date,
            superseded_by=superseded_by,
            equipment_ids=equipment_ids,
            language=lang,
            requires_manual_review=any(
                getattr(p, "error", None) is not None for p in pages
            ),
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

        # Register for future deduplication
        register_document(file_hash, file_hash, file.filename or "unknown")
        logger.info(
            f"Ingested: {file.filename} | type={doc_type} | pages={len(pages)} | {elapsed_ms:.0f}ms"
        )

        return result

    finally:
        # Always clean up temp file
        try:
            tmp_path.unlink(missing_ok=True)
        except Exception:
            pass
