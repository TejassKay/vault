"""FR-4, FR-5: Pydantic schemas for Appliance and Service."""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class ApplianceCreate(BaseModel):
    """FR-4: Confirm and save an appliance from an extracted bill."""

    bill_id: int | None = None
    category_id: int
    product_name: str
    brand: str | None = None
    model_number: str | None = None
    seller: str | None = None
    price: Decimal | None = Field(default=None, ge=0)
    purchase_date: date
    warranty_months: int = Field(default=0, ge=0)
    # corrected_fields: list of field names the user manually edited
    corrected_fields: dict[str, Any] | None = None


class ApplianceUpdate(BaseModel):
    """FR-4: Partial update of appliance fields."""

    product_name: str | None = None
    brand: str | None = None
    model_number: str | None = None
    seller: str | None = None
    price: Decimal | None = Field(default=None, ge=0)
    purchase_date: date | None = None
    warranty_months: int | None = Field(default=None, ge=0)
    category_id: int | None = None
    estimated_value: Decimal | None = None


class ServiceResponse(BaseModel):
    """FR-5: One service record."""

    model_config = ConfigDict(from_attributes=True)

    service_id: int
    appliance_id: int
    due_date: date
    status: str
    completed_on: date | None = None
    cost: Decimal | None = None
    guidance_label: str | None = None
    note: str | None = None


class ServiceUpdate(BaseModel):
    """PATCH /services/{id}: Mark service done."""

    status: str = "done"
    completed_on: date | None = None
    cost: Decimal | None = Field(default=None, ge=0)
    note: str | None = None


class ApplianceResponse(BaseModel):
    """FR-4, FR-5: Full appliance response with services."""

    model_config = ConfigDict(from_attributes=True)

    appliance_id: int
    user_id: int
    category_id: int
    bill_id: int | None = None
    product_name: str
    brand: str | None = None
    model_number: str | None = None
    seller: str | None = None
    price: Decimal | None = None
    purchase_date: date
    warranty_months: int
    warranty_end_date: date
    estimated_value: Decimal | None = None
    updated_at: datetime | None = None
    services: list[ServiceResponse] = []
