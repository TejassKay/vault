"""FR-4, FR-5, FR-6: Appliance confirmation, service schedule, and reminders."""

from __future__ import annotations

from datetime import date

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_user
from app.engines.service_scheduler import build_schedule, warranty_end_date
from app.models.appliance import ApplianceCategory, Service
from app.models.user import User
from app.repositories import appliance_repository
from app.schemas.appliance import (
    ApplianceCreate,
    ApplianceResponse,
    ApplianceUpdate,
    ServiceResponse,
    ServiceUpdate,
)
from app.services.reminder_service import (
    create_appliance_reminders,
    create_service_reminders,
)

router = APIRouter(tags=["appliances"])


# ---------------------------------------------------------------------------
# Appliances
# ---------------------------------------------------------------------------


@router.post("/appliances", response_model=ApplianceResponse, status_code=status.HTTP_201_CREATED)
def confirm_appliance(
    data: ApplianceCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ApplianceResponse:
    """FR-4, FR-5, FR-6: Confirm appliance; create service schedule and reminders."""
    # Validate category
    category = (
        db.query(ApplianceCategory)
        .filter(ApplianceCategory.category_id == data.category_id)
        .first()
    )
    if not category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Appliance category not found.",
        )

    today = date.today()
    w_end = warranty_end_date(data.purchase_date, data.warranty_months)

    # Create appliance
    appliance = appliance_repository.create_appliance(
        db,
        user_id=current_user.user_id,
        category_id=data.category_id,
        bill_id=data.bill_id,
        product_name=data.product_name,
        brand=data.brand,
        model_number=data.model_number,
        seller=data.seller,
        price=data.price,
        purchase_date=data.purchase_date,
        warranty_months=data.warranty_months,
        warranty_end_date=w_end,
    )

    # Update bill corrected_fields if provided
    if data.corrected_fields and data.bill_id:
        from app.repositories import bill_repository

        bill = bill_repository.get_bill(db, data.bill_id, current_user.user_id)
        if bill:
            bill_repository.update_bill(
                db,
                bill,
                corrected_fields=data.corrected_fields,
                parse_status="corrected",
            )

    # Build service schedule (pure function)
    schedule = build_schedule(
        purchase_date=data.purchase_date,
        warranty_months=data.warranty_months,
        interval_months=category.interval_months,
        guidance_source=category.guidance_source,
        today=today,
    )

    # Persist services
    service_records: list[Service] = []
    for svc_date in schedule:
        svc = Service(
            appliance_id=appliance.appliance_id,
            due_date=svc_date.due_date,
            status="pending",
            guidance_label=svc_date.guidance_label,
        )
        db.add(svc)
        service_records.append(svc)
    db.commit()

    # Refresh service IDs
    for svc in service_records:
        db.refresh(svc)

    # Create warranty reminders
    create_appliance_reminders(appliance, db, today)

    # Create service reminders
    for svc in service_records:
        create_service_reminders(svc, appliance, db, today)

    db.commit()
    db.refresh(appliance)
    return ApplianceResponse.model_validate(appliance)


@router.get("/appliances", response_model=list[ApplianceResponse])
def list_appliances(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[ApplianceResponse]:
    """FR-4, NFR-3: List user's appliances."""
    appliances = appliance_repository.get_appliances(db, current_user.user_id)
    return [ApplianceResponse.model_validate(a) for a in appliances]


@router.get("/appliances/{appliance_id}", response_model=ApplianceResponse)
def get_appliance(
    appliance_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ApplianceResponse:
    """FR-4, NFR-3: Get appliance by ID — owner only."""
    appliance = appliance_repository.get_appliance(db, appliance_id, current_user.user_id)
    if not appliance:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Appliance not found.")
    return ApplianceResponse.model_validate(appliance)


@router.patch("/appliances/{appliance_id}", response_model=ApplianceResponse)
def update_appliance(
    appliance_id: int,
    data: ApplianceUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ApplianceResponse:
    """FR-4: Partially update an appliance."""
    appliance = appliance_repository.get_appliance(db, appliance_id, current_user.user_id)
    if not appliance:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Appliance not found.")

    update_data = data.model_dump(exclude_none=True)

    # Recalculate warranty_end_date if relevant fields changed
    purchase_date = update_data.get("purchase_date", appliance.purchase_date)
    warranty_months = update_data.get("warranty_months", appliance.warranty_months)
    update_data["warranty_end_date"] = warranty_end_date(purchase_date, warranty_months)

    appliance_repository.update_appliance(db, appliance, **update_data)
    db.refresh(appliance)
    return ApplianceResponse.model_validate(appliance)


@router.delete("/appliances/{appliance_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_appliance(
    appliance_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> None:
    """FR-4: Delete an appliance and its services/reminders (cascade)."""
    appliance = appliance_repository.get_appliance(db, appliance_id, current_user.user_id)
    if not appliance:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Appliance not found.")
    appliance_repository.delete_appliance(db, appliance)


# ---------------------------------------------------------------------------
# Services
# ---------------------------------------------------------------------------


@router.patch("/services/{service_id}", response_model=ServiceResponse)
def update_service(
    service_id: int,
    data: ServiceUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ServiceResponse:
    """FR-5: Mark a service as done or update its details."""
    service = appliance_repository.get_service(db, service_id, current_user.user_id)
    if not service:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Service not found.")
    update_data = data.model_dump(exclude_none=True)
    appliance_repository.update_service(db, service, **update_data)
    return ServiceResponse.model_validate(service)
