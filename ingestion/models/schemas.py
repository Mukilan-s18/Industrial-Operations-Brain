from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class DocType(str, Enum):
    TEXT = "TEXT"
    SCANNED = "SCANNED"
    MIXED = "MIXED"
    TABLE_HEAVY = "TABLE_HEAVY"


class TableCell(BaseModel):
    row: int
    col: int
    value: str


class ExtractedTable(BaseModel):
    page: int
    markdown: str  # Human-readable markdown table for LLM consumption
    rows: list[list[str]]  # Raw row/col structure


class PageResult(BaseModel):
    page: int
    text: str = ""
    is_ocr: bool = False
    confidence: float | None = None  # Tesseract confidence, 0-100
    tables: list[ExtractedTable] = Field(default_factory=list)
    has_images: bool = False
    error: str | None = None


class DocumentMetadata(BaseModel):
    rev_number: str | None = None
    date: str | None = None
    superseded_by: str | None = None  # doc_id of newer version
    equipment_ids: list[str] = Field(default_factory=list)
    language: str = "en"
    requires_manual_review: bool = False
    has_version_conflict: bool = False


class IngestionResult(BaseModel):
    doc_id: str  # SHA-256 hash of file contents
    source: str  # Original filename
    doc_type: DocType
    pages: list[PageResult]
    metadata: DocumentMetadata
    total_pages: int
    processing_time_ms: float
    warnings: list[str] = Field(default_factory=list)


class IngestionError(BaseModel):
    source: str
    error: str
    detail: str | None = None


class HealthStatus(BaseModel):
    status: str  # "ok" | "degraded" | "error"
    tesseract_available: bool
    disk_space_ok: bool
    services: dict[str, Any] = Field(default_factory=dict)
