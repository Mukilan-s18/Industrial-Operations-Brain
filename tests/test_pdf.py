"""Tests for PDF text extraction."""

import sys
import tempfile
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))


def _create_simple_pdf(text: str) -> Path:
    """Create a minimal text PDF using PyMuPDF for testing."""
    import fitz

    doc = fitz.open()
    page = doc.new_page()
    page.insert_text((72, 72), text)
    tmp = tempfile.NamedTemporaryFile(suffix=".pdf", delete=False)
    doc.save(tmp.name)
    doc.close()
    return Path(tmp.name)


def test_pdf_extraction_returns_text():
    """Extracted text length must be > 0 for a valid PDF."""
    from ingestion.processors.pdf_processor import extract_pdf

    pdf_path = _create_simple_pdf(
        "Standard Operating Procedure Rev. 4\nP-101 valve inspection"
    )
    try:
        pages, doc_type = extract_pdf(pdf_path)
        full_text = " ".join(p.text for p in pages)
        assert len(full_text.strip()) > 0, "Extracted text should not be empty"
    finally:
        pdf_path.unlink(missing_ok=True)


def test_corrupt_pdf_raises_value_error():
    """Corrupt PDF should raise ValueError, not crash."""
    from ingestion.processors.pdf_processor import extract_pdf

    tmp = tempfile.NamedTemporaryFile(suffix=".pdf", delete=False)
    tmp.write(b"NOT A REAL PDF CONTENT!!!")
    tmp.close()

    try:
        with pytest.raises(ValueError):
            extract_pdf(Path(tmp.name))
    finally:
        Path(tmp.name).unlink(missing_ok=True)


def test_revision_extraction():
    """Revision number should be extracted from document text."""
    from ingestion.utils.metadata import extract_revision

    text = "Standard Operating Procedure\nRevision 4\nDate: 15/01/2024"
    rev = extract_revision(text)
    assert rev == "4", f"Expected '4', got '{rev}'"


def test_date_extraction():
    """Date should be extracted from document text."""
    from ingestion.utils.metadata import extract_date

    text = "Approved on 15/01/2024 by Engineering Manager"
    date = extract_date(text)
    assert date == "15/01/2024", f"Expected '15/01/2024', got '{date}'"


def test_equipment_id_extraction():
    """Equipment IDs like P-101, HV-204 should be found."""
    from ingestion.utils.metadata import extract_equipment_ids

    text = "Inspect valve P-101 and P-102. Check HV-204 before proceeding."
    ids = extract_equipment_ids(text)
    assert "P-101" in ids
    assert "P-102" in ids
    assert "HV-204" in ids


def test_document_deduplication():
    """Same file uploaded twice should be detected as duplicate."""
    from ingestion.utils.deduplication import (
        check_duplicate,
        register_document,
        clear_registry,
    )

    clear_registry()
    pdf_path = _create_simple_pdf("Test document for deduplication check")
    try:
        is_dup, file_hash, existing_id = check_duplicate(pdf_path)
        assert not is_dup, "First check should not be a duplicate"

        register_document(file_hash, file_hash, "test.pdf")

        is_dup2, _, existing_id2 = check_duplicate(pdf_path)
        assert is_dup2, "Second check should detect duplicate"
        assert existing_id2 == file_hash
    finally:
        pdf_path.unlink(missing_ok=True)
        clear_registry()


def test_file_validation_empty_file():
    """Empty file should fail validation."""
    from ingestion.utils.validation import validate_file

    tmp = tempfile.NamedTemporaryFile(suffix=".pdf", delete=False)
    tmp.close()
    try:
        is_valid, msg = validate_file(Path(tmp.name))
        assert not is_valid
        assert "empty" in msg.lower()
    finally:
        Path(tmp.name).unlink(missing_ok=True)
