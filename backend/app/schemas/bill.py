"""FR-2, FR-3: Pydantic schemas for Bill upload and extraction response."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict


class ExtractionFieldSchema(BaseModel):
    """One extracted field with its confidence score."""

    value: Any
    confidence: float  # 0.0 – 1.0


class BillResponse(BaseModel):
    """FR-2, FR-3: Response schema for a stored bill with extraction result."""

    model_config = ConfigDict(from_attributes=True)

    bill_id: int
    user_id: int
    file_url: str
    file_type: str
    parse_status: str
    raw_text: str | None = None
    extraction_json: dict[str, Any] | None = None
    corrected_fields: Any | None = None
    uploaded_at: datetime
    error: str | None = None


class BillCorrectRequest(BaseModel):
    """FR-4: User submits corrected field values."""

    corrected_fields: dict[str, Any]  # {field_name: corrected_value}
