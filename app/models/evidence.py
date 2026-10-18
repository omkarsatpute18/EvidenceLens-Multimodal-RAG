from datetime import datetime, timezone
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class ContentType(str, Enum):
    TEXT = "text"
    TABLE = "table"
    IMAGE = "image"
    CHART = "chart"


class EvidenceItem(BaseModel):
    evidence_id: str
    source_file: str
    source_type: str
    content_type: ContentType
    text_content: str = ""
    structured_content: dict[str, Any] = Field(default_factory=dict)
    page_number: int | None = None
    sheet_name: str | None = None
    row_start: int | None = None
    row_end: int | None = None
    column_start: str | None = None
    column_end: str | None = None
    image_reference: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)
    extraction_confidence: float = Field(default=1.0, ge=0, le=1)
    retrieval_score: float | None = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    @property
    def citation(self) -> str:
        location = self.source_file
        if self.page_number:
            location += f", p. {self.page_number}"
        if self.sheet_name:
            location += f", sheet {self.sheet_name}"
        if self.row_start:
            location += f", rows {self.row_start}-{self.row_end or self.row_start}"
        return f"[{self.evidence_id}] {location}"


class WorkflowEvent(BaseModel):
    label: str
    detail: str = ""
    status: str = "completed"


class Citation(BaseModel):
    evidence_id: str
    label: str
    source_file: str
    location: str = ""


class FinalAnswer(BaseModel):
    answer: str
    key_findings: list[str] = Field(default_factory=list)
    citations: list[Citation] = Field(default_factory=list)
    evidence_items: list[EvidenceItem] = Field(default_factory=list)
    confidence: float = 0.0
    contradictions: list[str] = Field(default_factory=list)
    limitations: list[str] = Field(default_factory=list)
    verification_status: str = "not_run"
    suggested_followups: list[str] = Field(default_factory=list)
    workflow_events: list[WorkflowEvent] = Field(default_factory=list)
