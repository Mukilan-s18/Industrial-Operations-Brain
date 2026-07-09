"""Tests for table extraction utilities."""

import sys
from pathlib import Path


sys.path.insert(0, str(Path(__file__).parent.parent))


def test_rows_to_markdown_basic():
    """Markdown table conversion should produce valid header/separator/body."""
    from ingestion.processors.table_processor import _rows_to_markdown

    rows = [
        ["Equipment ID", "Status", "Date"],
        ["P-101", "FAIL", "01/06/2024"],
        ["HV-204", "PASS", "02/06/2024"],
    ]
    md = _rows_to_markdown(rows)

    assert "| Equipment ID |" in md
    assert "| --- |" in md
    assert "| P-101 |" in md
    assert "| HV-204 |" in md


def test_rows_to_markdown_empty():
    """Empty rows should return empty string."""
    from ingestion.processors.table_processor import _rows_to_markdown

    assert _rows_to_markdown([]) == ""


def test_language_detection_english():
    """English text should be detected as 'en'."""
    from ingestion.utils.language import detect_language

    text = "Standard operating procedure for pump P-101 inspection and maintenance."
    lang, is_mixed = detect_language(text)
    assert lang == "en"
    assert not is_mixed


def test_language_detection_hindi():
    """Text with Devanagari characters should be flagged."""
    from ingestion.utils.language import flag_mixed_language

    # Mix of English and Hindi characters
    hindi_text = "पंप P-101 की जांच करें। Inspect valve P-101."
    result = flag_mixed_language(hindi_text)
    assert result["hindi_chars_present"] is True


def test_normalize_document_title():
    """Titles with revision markers should normalize to the same base."""
    from ingestion.utils.metadata import normalize_document_title

    title1 = normalize_document_title("SOP Pump P-101 Rev. 3")
    title2 = normalize_document_title("SOP Pump P-101 Rev. 4")
    assert title1 == title2, f"Normalized titles should match: '{title1}' vs '{title2}'"


def test_equipment_id_pattern():
    """Various equipment ID formats should be captured."""
    from ingestion.utils.metadata import extract_equipment_ids

    text = "Check P-101, HV-204, FCV-301, T-401, E-201, and LT-501 before startup."
    ids = extract_equipment_ids(text)
    for expected in ["P-101", "HV-204", "FCV-301", "T-401", "E-201", "LT-501"]:
        assert expected in ids, f"{expected} should be found in equipment IDs"
