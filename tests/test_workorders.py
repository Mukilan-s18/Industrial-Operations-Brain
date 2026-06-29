"""Tests for work order CSV/Excel parsing."""

import sys
import tempfile
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))


def _create_csv(content: str) -> Path:
    tmp = tempfile.NamedTemporaryFile(suffix=".csv", delete=False, mode="w", encoding="utf-8")
    tmp.write(content)
    tmp.close()
    return Path(tmp.name)


def test_work_order_csv_basic():
    """Standard columns should be parsed correctly."""
    from ingestion.processors.workorder_processor import extract_work_orders

    csv_content = (
        "equipment_id,failure_type,date,technician,resolution\n"
        "P-101,Valve leak,2024-01-15,John Smith,Replaced seal\n"
        "HV-204,Actuator failure,2024-01-16,Jane Doe,Replaced actuator\n"
    )
    path = _create_csv(csv_content)
    try:
        records = extract_work_orders(path)
        assert len(records) == 2
        assert records[0]["equipment_id"] == "P-101"
        assert records[1]["equipment_id"] == "HV-204"
        assert records[0]["failure_type"] == "Valve leak"
    finally:
        path.unlink(missing_ok=True)


def test_work_order_column_normalization():
    """Non-standard column names should be normalized."""
    from ingestion.processors.workorder_processor import extract_work_orders

    csv_content = (
        "EqpNum,Fault,Date,Tech,Notes\n"
        " p-101 ,Overheat,2024-02-01,Bob,Cleaned filter\n"
    )
    path = _create_csv(csv_content)
    try:
        records = extract_work_orders(path)
        assert len(records) == 1
        # Equipment ID should be normalized: " p-101 " → "P-101"
        assert records[0]["equipment_id"] == "P-101"
    finally:
        path.unlink(missing_ok=True)


def test_missing_equipment_id_flagged():
    """Records with missing equipment_id should be flagged for manual review."""
    from ingestion.processors.workorder_processor import extract_work_orders

    csv_content = (
        "equipment_id,failure_type,date,technician,resolution\n"
        ",Valve leak,2024-01-15,John Smith,Replaced seal\n"
    )
    path = _create_csv(csv_content)
    try:
        records = extract_work_orders(path)
        assert records[0]["requires_manual_review"] is True
        assert records[0]["equipment_id"] is None
    finally:
        path.unlink(missing_ok=True)


def test_cp1252_encoding():
    """CSV with cp1252 encoding should parse without errors."""
    from ingestion.processors.workorder_processor import extract_work_orders

    csv_content = "equipment_id,failure_type\nP-101,Valve clogged\n"
    tmp = tempfile.NamedTemporaryFile(suffix=".csv", delete=False, mode="wb")
    tmp.write(csv_content.encode("cp1252"))
    tmp.close()
    path = Path(tmp.name)
    try:
        records = extract_work_orders(path)
        assert len(records) == 1
        assert records[0]["equipment_id"] == "P-101"
    finally:
        path.unlink(missing_ok=True)
