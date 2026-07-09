"""
Excel Processor: Handles .xlsx/.xls spreadsheets and inspection sheets.
Handles merged cells, empty rows/columns, and industrial formatting quirks.
"""

import logging
from pathlib import Path
from typing import List

import pandas as pd

from ingestion.models.schemas import ExtractedTable, PageResult

logger = logging.getLogger(__name__)


def _clean_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """Clean up a DataFrame: drop empty rows/columns, forward-fill merged cells."""
    # Drop fully empty columns and rows
    df = df.dropna(how="all", axis=1).dropna(how="all", axis=0)
    # Forward-fill for merged cells (common in industrial inspection sheets)
    df = df.ffill()
    # Reset index
    df = df.reset_index(drop=True)
    return df


def _df_to_markdown(df: pd.DataFrame) -> str:
    """Convert a DataFrame to a Markdown table string."""
    if df.empty:
        return ""
    headers = [str(c) for c in df.columns.tolist()]
    rows = df.astype(str).values.tolist()
    separator = ["---"] * len(headers)
    lines = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join(separator) + " |",
    ]
    for row in rows:
        lines.append("| " + " | ".join(row) + " |")
    return "\n".join(lines)


def extract_excel(file_path: Path) -> List[PageResult]:
    """
    Extract all sheets from an Excel file.
    Each sheet becomes a PageResult (with tables list).
    """
    pages: List[PageResult] = []

    try:
        xl = pd.ExcelFile(str(file_path))
    except Exception as e:
        logger.error(f"Cannot open Excel file {file_path}: {e}")
        raise ValueError(f"Failed to open Excel file: {e}")

    for sheet_idx, sheet_name in enumerate(xl.sheet_names):
        try:
            df = xl.parse(sheet_name, header=0, dtype=str)
            df = _clean_dataframe(df)

            if df.empty:
                logger.info(f"Sheet '{sheet_name}' is empty, skipping")
                continue

            rows = df.astype(str).values.tolist()
            col_headers = [str(c) for c in df.columns.tolist()]
            all_rows = [col_headers] + rows

            table = ExtractedTable(
                page=sheet_idx + 1,
                markdown=_df_to_markdown(df),
                rows=all_rows,
            )

            pages.append(
                PageResult(
                    page=sheet_idx + 1,
                    text=f"Sheet: {sheet_name}\n\n" + _df_to_markdown(df),
                    is_ocr=False,
                    tables=[table],
                )
            )

        except Exception as e:
            logger.warning(f"Error processing sheet '{sheet_name}': {e}")
            pages.append(
                PageResult(
                    page=sheet_idx + 1,
                    text="",
                    is_ocr=False,
                    error=str(e),
                )
            )

    return pages
