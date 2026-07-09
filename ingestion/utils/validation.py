"""
Validation: File type and MIME type validation.
Trusts MIME type inspection over file extension to reject malicious files.
"""

import logging
import mimetypes
from pathlib import Path
from typing import Tuple

logger = logging.getLogger(__name__)

# Allowed MIME types and their expected extensions
ALLOWED_MIME_TYPES = {
    "application/pdf": [".pdf"],
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet": [".xlsx"],
    "application/vnd.ms-excel": [".xls"],
    "text/csv": [".csv"],
    "application/csv": [".csv"],
    "text/plain": [".csv", ".txt"],
}

MAX_FILE_SIZE_BYTES = 50 * 1024 * 1024  # 50 MB hard limit


def detect_mime_type(file_path: Path) -> str:
    """Detect MIME type using python-magic (content-based, not extension-based)."""
    try:
        import magic

        mime = magic.from_file(str(file_path), mime=True)
        return mime
    except ImportError:
        # Fallback to mimetypes (extension-based)
        mime, _ = mimetypes.guess_type(str(file_path))
        return mime or "application/octet-stream"
    except Exception as e:
        logger.warning(f"MIME detection failed: {e}, falling back to extension")
        mime, _ = mimetypes.guess_type(str(file_path))
        return mime or "application/octet-stream"


def validate_file(file_path: Path) -> Tuple[bool, str]:
    """
    Validate a file for ingestion.

    Returns:
        (is_valid, error_message_or_empty)
    """
    # Check file exists and is not empty
    if not file_path.exists():
        return False, "File does not exist"

    file_size = file_path.stat().st_size
    if file_size == 0:
        return False, "File is empty"

    if file_size > MAX_FILE_SIZE_BYTES:
        return False, f"File too large ({file_size / 1024 / 1024:.1f} MB). Max 50 MB."

    # Detect and validate MIME type
    detected_mime = detect_mime_type(file_path)
    if detected_mime not in ALLOWED_MIME_TYPES:
        return False, (
            f"Unsupported file type: {detected_mime}. "
            f"Allowed types: PDF, XLSX, XLS, CSV"
        )

    logger.info(f"Validated: {file_path.name} ({detected_mime}, {file_size} bytes)")
    return True, ""


def get_file_category(file_path: Path) -> str:
    """Return 'pdf', 'excel', or 'csv' based on detected MIME type."""
    mime = detect_mime_type(file_path)
    if mime == "application/pdf":
        return "pdf"
    if mime in (
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        "application/vnd.ms-excel",
    ):
        return "excel"
    if mime in ("text/csv", "application/csv", "text/plain"):
        return "csv"
    return "unknown"
