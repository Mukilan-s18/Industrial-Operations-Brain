"""
Deduplication: SHA-256 based file deduplication.
Maintains an in-memory registry. Can be extended to persist to SQLite/Redis.
"""

import logging
from pathlib import Path
from threading import Lock
from typing import Dict, Optional, Tuple

from ingestion.utils.metadata import compute_file_hash

logger = logging.getLogger(__name__)

# In-memory registry: hash -> (doc_id, source_filename)
_registry: Dict[str, Tuple[str, str]] = {}
_lock = Lock()


def check_duplicate(file_path: Path) -> Tuple[bool, str, Optional[str]]:
    """
    Check if a file has already been ingested.

    Returns:
        (is_duplicate, file_hash, existing_doc_id or None)
    """
    file_hash = compute_file_hash(file_path)
    with _lock:
        if file_hash in _registry:
            existing_doc_id, existing_source = _registry[file_hash]
            logger.info(
                f"Duplicate detected: {file_path.name} matches existing doc "
                f"'{existing_source}' (id={existing_doc_id})"
            )
            return True, file_hash, existing_doc_id
    return False, file_hash, None


def register_document(file_hash: str, doc_id: str, source: str) -> None:
    """Register a successfully ingested document."""
    with _lock:
        _registry[file_hash] = (doc_id, source)


def clear_registry() -> None:
    """Clear the deduplication registry (used for demo resets)."""
    with _lock:
        _registry.clear()
    logger.info("Deduplication registry cleared")


def get_registry_size() -> int:
    """Return number of documents currently registered."""
    with _lock:
        return len(_registry)
