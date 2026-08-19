from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class Equipment(BaseModel):
    id: str = Field(..., description="Unique equipment tag, e.g. P-101")
    type: str = Field(..., description="Type of equipment, e.g., Pump, Compressor")
    location: str | None = Field(
        None, description="Physical location of the equipment"
    )


class Regulation(BaseModel):
    id: str = Field(..., description="Regulation reference identifier, e.g. OISD-118")
    clause: str | None = Field(None, description="Specific clause of the regulation")
    authority: str = Field(..., description="Governing authority, e.g., OISD, PESO")


class FailureMode(BaseModel):
    type: str = Field(
        ..., description="Type of failure, e.g., Seal Leak, Bearing Seizure"
    )
    date: str | None = Field(None, description="Date of occurrence")
    severity: str | None = Field(None, description="Severity level")


class Parameter(BaseModel):
    name: str = Field(
        ..., description="Name of the parameter, e.g., Discharge Pressure"
    )
    value: str | None = Field(
        None, description="Parameter value, e.g. 4.5 bar, 82 C"
    )


class Person(BaseModel):
    name: str = Field(..., description="Name of the person")
    role: str | None = Field(None, description="Role of the person")


class Document(BaseModel):
    id: str = Field(..., description="Document identifier")
    title: str = Field(..., description="Title of the document")
    author: str | None = Field(None, description="Author of the document")
    date: str | None = Field(None, description="Date of the document")


# Entity extraction output wrapper
class ExtractedEntity(BaseModel):
    id: str
    label: str  # EQUIPMENT, REGULATION, FAILURE_MODE, PARAMETER, PERSON, DATE, etc.
    span_start: int
    span_end: int
    text: str
    properties: dict[str, Any] = Field(default_factory=dict)


class ExtractedDocumentEntities(BaseModel):
    doc_id: str
    entities: list[ExtractedEntity]


class GraphEdge(BaseModel):
    source: str
    target: str
    type: str
    confidence: float = 1.0
    weight: int = 1
    properties: dict[str, Any] = Field(default_factory=dict)


class KnowledgeGraphSchema(BaseModel):
    nodes: dict[str, dict[str, Any]]
    edges: list[GraphEdge]
