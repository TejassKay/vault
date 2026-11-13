"""FR-4, FR-5, NFR-3: Appliance and Service repository — always filters by user_id."""

from __future__ import annotations

from sqlalchemy.orm import Session

from app.models.appliance import Appliance, Service

# ---------------------------------------------------------------------------
# Appliance
# ---------------------------------------------------------------------------


def get_appliance(db: Session, appliance_id: int, user_id: int) -> Appliance | None:
    return (
        db.query(Appliance)
        .filter(Appliance.appliance_id == appliance_id, Appliance.user_id == user_id)
        .first()
    )


def get_appliances(db: Session, user_id: int) -> list[Appliance]:
    return (
        db.query(Appliance)
        .filter(Appliance.user_id == user_id)
        .order_by(Appliance.purchase_date.desc())
        .all()
    )


def create_appliance(db: Session, **kwargs: object) -> Appliance:
    appliance = Appliance(**kwargs)
    db.add(appliance)
    db.commit()
    db.refresh(appliance)
    return appliance


def update_appliance(db: Session, appliance: Appliance, **kwargs: object) -> Appliance:
    for key, value in kwargs.items():
        setattr(appliance, key, value)
    db.commit()
    db.refresh(appliance)
    return appliance


def delete_appliance(db: Session, appliance: Appliance) -> None:
    db.delete(appliance)
    db.commit()


# ---------------------------------------------------------------------------
# Service
# ---------------------------------------------------------------------------


def get_service(db: Session, service_id: int, user_id: int) -> Service | None:
    """Return service record only if the appliance belongs to user_id."""
    return (
        db.query(Service)
        .join(Appliance, Appliance.appliance_id == Service.appliance_id)
        .filter(Service.service_id == service_id, Appliance.user_id == user_id)
        .first()
    )


def update_service(db: Session, service: Service, **kwargs: object) -> Service:
    for key, value in kwargs.items():
        setattr(service, key, value)
    db.commit()
    db.refresh(service)
    return service
