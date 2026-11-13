import json
from pathlib import Path

from sqlalchemy.orm import Session

from app.core.database import SessionLocal
from app.models.appliance import ApplianceCategory


def seed_service_intervals(db: Session | None = None) -> int:
    """Idempotently seed appliance categories and service intervals from JSON."""
    close_session = False
    if db is None:
        db = SessionLocal()
        close_session = True

    try:
        json_path = Path(__file__).parent / "service_intervals.json"
        with open(json_path, encoding="utf-8") as f:
            categories_data = json.load(f)

        count = 0
        for item in categories_data:
            existing = (
                db.query(ApplianceCategory).filter(ApplianceCategory.name == item["name"]).first()
            )
            if not existing:
                category = ApplianceCategory(
                    name=item["name"],
                    interval_months=item["interval_months"],
                    tips=item.get("tips"),
                    guidance_source=item.get("guidance_source", "general"),
                )
                db.add(category)
                count += 1
            else:
                # Update properties if changed
                existing.interval_months = item["interval_months"]
                existing.tips = item.get("tips")
                existing.guidance_source = item.get("guidance_source", "general")

        db.commit()
        return count
    finally:
        if close_session:
            db.close()


if __name__ == "__main__":
    inserted = seed_service_intervals()
    print(f"Seeded {inserted} new appliance categories successfully.")
