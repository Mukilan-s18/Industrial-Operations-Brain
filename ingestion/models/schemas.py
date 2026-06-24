from pydantic import BaseModel, Field
from typing import Optional, List, Any, Dict
from enum import Enum


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
    rows: List[List[str]]  # Raw row/col structure


class PageResult(BaseModel):
    page: int
    text: str = ""
    is_ocr: bool = False
    confidence: Optional[float] = None  # Tesseract confidence, 0-100
    tables: List[ExtractedTable] = Field(default_factory=list)
    has_images: bool = False
    error: Optional[str] = None


class DocumentMetadata(BaseModel):
    rev_number: Optional[str] = None
    date: Optional[str] = None
    superseded_by: Optional[str] = None  # doc_id of newer version
    equipment_ids: List[str] = Field(default_factory=list)
    language: str = "en"
    requires_manual_review: bool = False
    has_version_conflict: bool = False


class IngestionResult(BaseModel):
    doc_id: str  # SHA-256 hash of file contents
    source: str  # Original filename
    doc_type: DocType
    pages: List[PageResult]
    metadata: DocumentMetadata
    total_pages: int
    processing_time_ms: float
    warnings: List[str] = Field(default_factory=list)


class IngestionError(BaseModel):
    source: str
    error: str
    detail: Optional[str] = None


class HealthStatus(BaseModel):
    status: str  # "ok" | "degraded" | "error"
    tesseract_available: bool
    disk_space_ok: bool
    services: Dict[str, Any] = Field(default_factory=dict)
