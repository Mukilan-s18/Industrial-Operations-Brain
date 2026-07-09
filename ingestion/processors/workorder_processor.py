"""
Work Order Processor: Parses CSV/Excel maintenance work orders.
Normalizes column names to standard schema and validates equipment IDs.
"""

import logging
import re
from pathlib import Path
from typing import Any, Dict, List, Optional

import pandas as pd

logger = logging.getLogger(__name__)

# Mapping of raw column name variants → standard schema fields
COLUMN_MAP = {
    "equipment_id": [
        "equipment_id",
        "eqpnum",
        "assetid",
        "asset_id",
        "equip_id",
        "equipment",
        "asset",
        "machine_id",
        "equipmentid",
        "eq_id",
        "eq id",
        "asset no",
        "equip no",
    ],
    "failure_type": [
        "failure_type",
        "failure",
        "fault",
        "fault_type",
        "issue",
        "problem",
        "defect",
        "failure type",
        "fault type",
    ],
    "date": [
        "date",
        "wo_date",
        "work_order_date",
        "reported_date",
        "event_date",
        "date_reported",
        "date reported",
    ],
    "technician": [
        "technician",
        "tech",
        "technician_name",
        "assigned_to",
        "operator",
        "engineer",
        "mechanic",
        "technician name",
    ],
    "resolution": [
        "resolution",
        "action",
        "corrective_action",
        "fix",
        "resolution_notes",
        "action_taken",
        "notes",
        "remarks",
        "corrective action",
    ],
}

EQUIPMENT_ID_PATTERN = re.compile(r"^[A-Z0-9][A-Z0-9\-]{1,19}$")


def _normalize_column_names(df: pd.DataFrame) -> pd.DataFrame:
    """Map raw column names to standard schema names."""
    col_lower = {col: col.strip().lower() for col in df.columns}
    rename_map: Dict[str, str] = {}

    for standard, variants in COLUMN_MAP.items():
        for raw_col, lower_col in col_lower.items():
            if lower_col in variants and standard not in rename_map.values():
                rename_map[raw_col] = standard
                break

    return df.rename(columns=rename_map)


def _normalize_equipment_id(raw_id: Any) -> Optional[str]:
    """
    Normalize equipment ID:
    - Strip whitespace
    - Force uppercase
    - Validate format
    Returns None if invalid/missing.
    """
    if pd.isna(raw_id) or str(raw_id).strip() in ("", "nan", "None"):
        return None
    normalized = str(raw_id).strip().upper()
    return normalized


def extract_work_orders(file_path: Path) -> List[Dict[str, Any]]:
    """
    Parse work order records from CSV or Excel.

    Returns:
        List of standardized work order dicts ready for knowledge graph linking.
    """
    ext = file_path.suffix.lower()
    records: List[Dict[str, Any]] = []

    try:
        if ext == ".csv":
            # Try multiple encodings — industrial data often uses cp1252
            for encoding in ("utf-8", "cp1252", "latin-1"):
                try:
                    df = pd.read_csv(str(file_path), dtype=str, encoding=encoding)
                    break
                except UnicodeDecodeError:
                    continue
            else:
                raise ValueError("Could not decode CSV with utf-8, cp1252, or latin-1")

        elif ext in (".xlsx", ".xls"):
            df = pd.read_excel(str(file_path), dtype=str)
        else:
            raise ValueError(f"Unsupported work order format: {ext}")

    except Exception as e:
        logger.error(f"Failed to read work order file {file_path}: {e}")
        raise

    # Drop fully empty rows
    df = df.dropna(how="all").reset_index(drop=True)
    df = _normalize_column_names(df)

    for idx, row in df.iterrows():
        equipment_id_raw = row.get("equipment_id", None)
        equipment_id = _normalize_equipment_id(equipment_id_raw)
        requires_review = False

        if equipment_id is None:
            logger.warning(
                f"Row {idx}: Missing equipment_id — flagged for manual review"
            )
            requires_review = True

        record: Dict[str, Any] = {
            "equipment_id": equipment_id,
            "failure_type": str(row.get("failure_type", "")).strip() or None,
            "date": str(row.get("date", "")).strip() or None,
            "technician": str(row.get("technician", "")).strip() or None,
            "resolution": str(row.get("resolution", "")).strip() or None,
            "requires_manual_review": requires_review,
            "_raw_row": row.to_dict(),  # Keep raw for debugging
        }
        records.append(record)

    logger.info(f"Parsed {len(records)} work order records from {file_path.name}")
    return records
