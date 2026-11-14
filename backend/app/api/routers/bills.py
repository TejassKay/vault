"""FR-2, FR-3, FR-4: Bill upload and retrieval endpoints."""

from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_user
from app.models.user import User
from app.repositories import bill_repository
from app.schemas.bill import BillCorrectRequest, BillResponse
from app.services.bill_parser import BillParser

router = APIRouter(prefix="/bills", tags=["bills"])

# FR-2: 10 MB max
MAX_FILE_SIZE = 10 * 1024 * 1024
ALLOWED_TYPES = {
    "application/pdf": "pdf",
    "image/jpeg": "jpg",
    "image/png": "png",
}

# Directory for uploaded bills
UPLOAD_DIR = Path(__file__).resolve().parent.parent.parent.parent / "uploads"


def _get_file_type(content_type: str, filename: str) -> str:
    """Determine file type from MIME type or extension."""
    if content_type in ALLOWED_TYPES:
        return ALLOWED_TYPES[content_type]
    ext = Path(filename or "").suffix.lower().lstrip(".")
    if ext in ("pdf", "jpg", "jpeg", "png"):
        return "jpg" if ext == "jpeg" else ext
    raise HTTPException(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        detail="File must be PDF, JPG, or PNG.",
    )


@router.post("", response_model=BillResponse, status_code=status.HTTP_201_CREATED)
async def upload_bill(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> BillResponse:
    """FR-2, FR-3: Upload a bill file, extract fields, return structured result."""
    # Validate MIME type
    file_type = _get_file_type(file.content_type or "", file.filename or "")

    # Read and validate size
    contents = await file.read()
    if len(contents) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="File must be 10 MB or less.",
        )

    # Save file
    user_dir = UPLOAD_DIR / str(current_user.user_id)
    user_dir.mkdir(parents=True, exist_ok=True)
    safe_name = Path(file.filename or "bill").name
    file_path = user_dir / safe_name
    # Avoid name collisions by appending bill_id-like random suffix
    import uuid

    unique_name = f"{uuid.uuid4().hex}_{safe_name}"
    file_path = user_dir / unique_name
    file_path.write_bytes(contents)

    # Create pending bill record
    relative_url = f"/uploads/{current_user.user_id}/{unique_name}"
    bill = bill_repository.create_bill(
        db,
        user_id=current_user.user_id,
        file_url=relative_url,
        file_type=file_type,
        parse_status="pending",
    )

    # Parse
    parser = BillParser()
    result = parser.extract(str(file_path), file_type)

    # Update bill with parsed data
    bill = bill_repository.update_bill(
        db,
        bill,
        raw_text=result["raw_text"],
        extraction_json=result["extraction_json"],
        parse_status=result["parse_status"],
    )

    resp = BillResponse.model_validate(bill)
    if result.get("error"):
        resp.error = result["error"]
    return resp


@router.get("/{bill_id}", response_model=BillResponse)
def get_bill(
    bill_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> BillResponse:
    """FR-2, NFR-3: Get bill by ID — owner only."""
    bill = bill_repository.get_bill(db, bill_id, current_user.user_id)
    if not bill:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Bill not found.")
    return BillResponse.model_validate(bill)


@router.patch("/{bill_id}/correct", response_model=BillResponse)
def correct_bill(
    bill_id: int,
    data: BillCorrectRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> BillResponse:
    """FR-4: User submits corrections; mark parse_status='corrected', record corrected fields."""
    bill = bill_repository.get_bill(db, bill_id, current_user.user_id)
    if not bill:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Bill not found.")

    # Merge corrected values into extraction_json
    extraction = dict(bill.extraction_json or {})
    for field, corrected_value in data.corrected_fields.items():
        if field in extraction:
            extraction[field] = {"value": corrected_value, "confidence": 1.0, "corrected": True}
        else:
            extraction[field] = {"value": corrected_value, "confidence": 1.0, "corrected": True}

    bill = bill_repository.update_bill(
        db,
        bill,
        extraction_json=extraction,
        corrected_fields=data.corrected_fields,
        parse_status="corrected",
    )
    return BillResponse.model_validate(bill)
