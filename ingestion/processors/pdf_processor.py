"""
PDF Processor: Handles text-layer PDFs using PyMuPDF (fitz).
Falls back to OCR for image-only pages via ocr_processor.
"""

import logging
from pathlib import Path
from typing import List

import fitz  # PyMuPDF

from ingestion.models.schemas import DocType, ExtractedTable, PageResult
from ingestion.processors.ocr_processor import ocr_page
from ingestion.processors.table_processor import extract_tables_from_page

logger = logging.getLogger(__name__)

# If a page has less than this many characters, treat it as image-only
TEXT_THRESHOLD = 30


def classify_doc_type(pages: List[PageResult]) -> DocType:
    """Classify the document type based on page content."""
    if not pages:
        return DocType.TEXT

    ocr_pages = sum(1 for p in pages if p.is_ocr)
    total_pages = len(pages)
    total_chars = sum(len(p.text) for p in pages)
    table_chars = sum(
        sum(len(cell) for row in t.rows for cell in row)
        for p in pages
        for t in p.tables
    )

    if ocr_pages == total_pages:
        return DocType.SCANNED
    if ocr_pages > 0:
        return DocType.MIXED
    if total_chars > 0 and table_chars / total_chars > 0.5:
        return DocType.TABLE_HEAVY
    return DocType.TEXT


def extract_pdf(file_path: Path) -> tuple[List[PageResult], DocType]:
    """
    Extract text and tables from a PDF file.

    Returns:
        (pages, doc_type) where pages is a list of PageResult objects
    """
    pages: List[PageResult] = []

    try:
        doc = fitz.open(str(file_path))
    except fitz.FileDataError as e:
        logger.error(f"Corrupt PDF file: {file_path} — {e}")
        raise ValueError(f"Corrupt or unreadable PDF: {e}")
    except Exception as e:
        logger.error(f"Failed to open PDF: {file_path} — {e}")
        raise ValueError(f"Could not open file: {e}")

    for page_num in range(len(doc)):
        try:
            page = doc[page_num]
            text = page.get_text("text").strip()

            if len(text) < TEXT_THRESHOLD:
                # Page appears to be image-only → OCR it
                logger.info(f"Page {page_num + 1}: no text layer, running OCR")
                page_result = ocr_page(page, page_num + 1)
            else:
                # Extract tables (pdfplumber handles this better)
                tables = extract_tables_from_page(file_path, page_num)
                page_result = PageResult(
                    page=page_num + 1,
                    text=text,
                    is_ocr=False,
                    tables=tables,
                )

            pages.append(page_result)

        except Exception as e:
            logger.warning(f"Error processing page {page_num + 1}: {e}")
            pages.append(
                PageResult(
                    page=page_num + 1,
                    text="",
                    is_ocr=False,
                    error=str(e),
                )
            )

    doc.close()
    doc_type = classify_doc_type(pages)
    return pages, doc_type
