"""
Table Processor: Extracts structured tables from PDFs.
Uses camelot (lattice first, then stream) with pdfplumber as fallback.
Outputs tables as both Markdown strings (for LLMs) and raw row/col lists.
"""

import logging
from pathlib import Path
from typing import List

import pdfplumber

from ingestion.models.schemas import ExtractedTable

logger = logging.getLogger(__name__)


def _rows_to_markdown(rows: List[List[str]]) -> str:
    """Convert a list of rows to a Markdown table string."""
    if not rows:
        return ""

    # Clean cells
    clean_rows = [
        [str(cell).strip() if cell is not None else "" for cell in row] for row in rows
    ]

    header = clean_rows[0]
    separator = ["---"] * len(header)
    body = clean_rows[1:] if len(clean_rows) > 1 else []

    lines = [
        "| " + " | ".join(header) + " |",
        "| " + " | ".join(separator) + " |",
    ]
    for row in body:
        lines.append("| " + " | ".join(row) + " |")

    return "\n".join(lines)


def extract_tables_camelot(file_path: Path, page_num: int) -> List[ExtractedTable]:
    """Extract tables using camelot (lattice → stream fallback)."""
    tables: List[ExtractedTable] = []
    page_str = str(page_num + 1)  # camelot uses 1-indexed string

    try:
        import camelot

        # Try lattice flavor first (good for tables with grid lines)
        result = camelot.read_pdf(
            str(file_path), pages=page_str, flavor="lattice", suppress_stdout=True
        )
        if result.n == 0:
            # Fallback to stream flavor (whitespace-based)
            result = camelot.read_pdf(
                str(file_path), pages=page_str, flavor="stream", suppress_stdout=True
            )

        for tbl in result:
            rows = tbl.df.values.tolist()
            if rows:
                tables.append(
                    ExtractedTable(
                        page=page_num + 1,
                        markdown=_rows_to_markdown(rows),
                        rows=[[str(c) for c in row] for row in rows],
                    )
                )

    except ImportError:
        logger.warning("camelot not available, falling back to pdfplumber")
    except Exception as e:
        logger.warning(
            f"camelot failed on page {page_num + 1}: {e} — trying pdfplumber"
        )

    return tables


def extract_tables_pdfplumber(file_path: Path, page_num: int) -> List[ExtractedTable]:
    """Extract tables using pdfplumber as fallback."""
    tables: List[ExtractedTable] = []
    try:
        with pdfplumber.open(str(file_path)) as pdf:
            if page_num >= len(pdf.pages):
                return tables
            page = pdf.pages[page_num]
            raw_tables = page.extract_tables()
            for raw in raw_tables:
                if raw:
                    rows = [
                        [str(cell) if cell is not None else "" for cell in row]
                        for row in raw
                    ]
                    tables.append(
                        ExtractedTable(
                            page=page_num + 1,
                            markdown=_rows_to_markdown(rows),
                            rows=rows,
                        )
                    )
    except Exception as e:
        logger.warning(
            f"pdfplumber table extraction failed on page {page_num + 1}: {e}"
        )

    return tables


def extract_tables_from_page(file_path: Path, page_num: int) -> List[ExtractedTable]:
    """
    Main entry: try camelot first, fall back to pdfplumber.
    Returns tables with both Markdown string and raw row/col structure.
    """
    tables = extract_tables_camelot(file_path, page_num)
    if not tables:
        tables = extract_tables_pdfplumber(file_path, page_num)
    return tables
