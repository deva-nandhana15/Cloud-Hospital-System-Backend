import os
import shutil
import uuid
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session
from typing import List, Optional

from app.db.database import get_db
from app.models.models import LabReport, Patient, User, UserRole
from app.schemas.lab_report import LabReportResponse
from app.api.deps import get_current_active_user, require_role

router = APIRouter()

UPLOAD_DIR = Path("uploads/lab_reports")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


def build_lab_response(report, db):
    patient = db.query(Patient).filter(Patient.id == report.patient_id).first()

    return LabReportResponse(
        id=report.id,
        patient_id=report.patient_id,
        appointment_id=report.appointment_id,
        uploaded_by=report.uploaded_by,
        file_name=report.file_name,
        extracted_data=report.extracted_data,
        flagged_values=report.flagged_values,
        status=report.status,
        created_at=report.created_at,
        patient_name=patient.full_name if patient else None,
    )


@router.post("/upload", response_model=LabReportResponse)
async def upload_lab_report(
    patient_id: int = Form(...),
    appointment_id: Optional[int] = Form(None),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_role(UserRole.admin, UserRole.nurse, UserRole.receptionist)
    ),
):
    patient = db.query(Patient).filter(Patient.id == patient_id).first()
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")

    ext = Path(file.filename or "").suffix or ""
    safe_name = f"{uuid.uuid4().hex}{ext}"
    file_path = UPLOAD_DIR / safe_name

    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    display_name = file.filename or safe_name

    new_report = LabReport(
    patient_id=patient_id,
    appointment_id=appointment_id,
    uploaded_by=current_user.id,
    file_name=file.filename,
    file_path=file_path,
    status="pending"  # ← stays as pending until doctor reviews
    )
    db.add(new_report)
    db.commit()
    db.refresh(new_report)

    return build_lab_response(new_report, db)


@router.get("/", response_model=List[LabReportResponse])
def get_all_reports(
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_role(
            UserRole.admin,
            UserRole.doctor,
            UserRole.nurse,
            UserRole.receptionist,
        )
    ),
):
    reports = db.query(LabReport).all()
    return [build_lab_response(r, db) for r in reports]


@router.get("/patient/{patient_id}", response_model=List[LabReportResponse])
def get_patient_reports(
    patient_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_role(
            UserRole.admin,
            UserRole.doctor,
            UserRole.nurse,
            UserRole.receptionist,
        )
    ),
):
    reports = db.query(LabReport).filter(
        LabReport.patient_id == patient_id
    ).all()
    return [build_lab_response(r, db) for r in reports]
