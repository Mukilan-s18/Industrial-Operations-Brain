"""
Metadata Utilities: Extract revision numbers, dates, and equipment IDs from text.
Also handles version conflict detection between documents.
"""

import hashlib
import logging
import re
from pathlib import Path
from typing import List, Optional

logger = logging.getLogger(__name__)

# Revision patterns: "Rev. 4", "Revision 4", "REV4", "Rev-4"
REV_PATTERNS = [
    re.compile(r"Rev(?:ision)?[.\-\s]*(\d+)", re.IGNORECASE),
    re.compile(r"REV[.\-\s]*(\d+)", re.IGNORECASE),
    re.compile(r"Version\s+(\d+(?:\.\d+)?)", re.IGNORECASE),
    re.compile(r"v(\d+(?:\.\d+)?)(?:\s|$)", re.IGNORECASE),
]

# Date patterns: DD/MM/YYYY, MM/DD/YYYY, YYYY-MM-DD, "15 Jan 2024"
DATE_PATTERNS = [
    re.compile(r"\b(\d{2}/\d{2}/\d{4})\b"),
    re.compile(r"\b(\d{4}-\d{2}-\d{2})\b"),
    re.compile(
        r"\b(\d{1,2}\s+(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{4})\b",
        re.IGNORECASE,
    ),
]

# Equipment ID patterns: P-101, HV-204, FCV-301, T-1, E-100A
EQUIPMENT_ID_PATTERN = re.compile(r"\b([A-Z]{1,4}-\d{1,4}[A-Z]?)\b")


def extract_revision(text: str, max_pages: int = 3) -> Optional[str]:
    """
    Search for revision number in text (scoped to first few pages).
    Returns the highest revision number found.
    """
    found_revs = []
    for pattern in REV_PATTERNS:
        matches = pattern.findall(text)
        found_revs.extend(matches)

    if not found_revs:
        return None

    # Return the maximum revision (handles multiple matches)
    try:
        return str(max(found_revs, key=lambda x: float(x)))
    except ValueError:
        return found_revs[0]


def extract_date(text: str) -> Optional[str]:
    """Extract the first recognizable date from text."""
    for pattern in DATE_PATTERNS:
        match = pattern.search(text)
        if match:
            return match.group(1)
    return None


def extract_equipment_ids(text: str) -> List[str]:
    """Extract all equipment IDs (e.g., P-101, HV-204) from text."""
    matches = EQUIPMENT_ID_PATTERN.findall(text)
    # Deduplicate and sort
    return sorted(set(matches))


def normalize_document_title(title: str) -> str:
    """Normalize a document title for version comparison."""
    # Remove revision indicators and extra whitespace
    title = re.sub(r"Rev(?:ision)?[.\-\s]*\d+", "", title, flags=re.IGNORECASE)
    title = re.sub(r"Version\s+\d+(?:\.\d+)?", "", title, flags=re.IGNORECASE)
    title = re.sub(r"\s+", " ", title).strip().lower()
    return title


def compute_file_hash(file_path: Path) -> str:
    """Compute SHA-256 hash of file contents for deduplication."""
    sha256 = hashlib.sha256()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            sha256.update(chunk)
    return sha256.hexdigest()
