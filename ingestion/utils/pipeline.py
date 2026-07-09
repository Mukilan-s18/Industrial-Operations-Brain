import json
from pathlib import Path
from typing import Tuple, List
from ingestion.models.schemas import DocType, PageResult


def run_extraction_pipeline(
    tmp_path: Path, category: str
) -> Tuple[List[PageResult], DocType, List[str]]:
    warnings = []

    if category == "pdf":
        from ingestion.processors.pdf_processor import extract_pdf

        pages, doc_type = extract_pdf(tmp_path)
    elif category == "excel":
        from ingestion.processors.excel_processor import extract_excel

        pages = extract_excel(tmp_path)
        doc_type = DocType.TABLE_HEAVY
    elif category == "csv":
        from ingestion.processors.workorder_processor import extract_work_orders

        records = extract_work_orders(tmp_path)
        text = json.dumps(records, indent=2, default=str)
        pages = [PageResult(page=1, text=text, is_ocr=False)]
        doc_type = DocType.TABLE_HEAVY
        if any(r.get("requires_manual_review", False) for r in records):
            warnings.append(
                "Some work order records missing equipment_id — require manual review."
            )
    else:
        raise ValueError(f"Unsupported file category: {category}")

    return pages, doc_type, warnings
