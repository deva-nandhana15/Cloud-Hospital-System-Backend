from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from app.db.database import get_db
from app.models.models import Patient, PatientVitals, User,UserRole, Doctor, Appointment
from app.schemas.patient import PatientCreate, PatientUpdate, PatientResponse, VitalsCreate, VitalsResponse
from app.api.deps import get_current_active_user, require_role

router = APIRouter()

# ─── Create Patient (Admin/Receptionist only) ─────────────
@router.post("/", response_model=PatientResponse)
def create_patient(
    patient_data: PatientCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(
        UserRole.admin, UserRole.receptionist
    ))
):
    new_patient = Patient(
        **patient_data.model_dump(),
        registered_by=current_user.id
    )
    db.add(new_patient)
    db.commit()
    db.refresh(new_patient)
    return new_patient

# ─── Get All Patients ─────────────────────────────────────
# ─── Get All Patients ─────────────────────────────────────
@router.get("/", response_model=List[PatientResponse])
def get_all_patients(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(
        UserRole.admin, UserRole.doctor,
        UserRole.receptionist, UserRole.nurse
    ))
):
    # Doctor can only see patients they have appointments with
    if current_user.role == UserRole.doctor:
        doctor = db.query(Doctor).filter(
            Doctor.user_id == current_user.id
        ).first()
        if not doctor:
            return []
        # Get patient IDs from doctor's appointments
        appointments = db.query(Appointment).filter(
            Appointment.doctor_id == doctor.id
        ).all()
        patient_ids = list(set([a.patient_id for a in appointments]))
        if not patient_ids:
            return []
        return db.query(Patient).filter(
            Patient.id.in_(patient_ids)
        ).all()

    # Admin, Receptionist, Nurse see all patients
    return db.query(Patient).all()

# ─── Get Patient by ID ────────────────────────────────────
@router.get("/{patient_id}", response_model=PatientResponse)
def get_patient(
    patient_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    patient = db.query(Patient).filter(Patient.id == patient_id).first()
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")
    return patient

# ─── Update Patient ───────────────────────────────────────
@router.put("/{patient_id}", response_model=PatientResponse)
def update_patient(
    patient_id: int,
    patient_data: PatientUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(
        UserRole.admin, UserRole.receptionist
    ))
):
    patient = db.query(Patient).filter(Patient.id == patient_id).first()
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")
    for field, value in patient_data.model_dump(exclude_unset=True).items():
        setattr(patient, field, value)
    db.commit()
    db.refresh(patient)
    return patient

# ─── Delete Patient (Admin only) ──────────────────────────
@router.delete("/{patient_id}")
def delete_patient(
    patient_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.admin))
):
    patient = db.query(Patient).filter(Patient.id == patient_id).first()
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")
    db.delete(patient)
    db.commit()
    return {"message": "Patient deleted successfully"}

# ─── Add Vitals (Nurse only) ──────────────────────────────
@router.post("/vitals/add", response_model=VitalsResponse)
def add_vitals(
    vitals_data: VitalsCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(
        UserRole.nurse, UserRole.admin
    ))
):
    patient = db.query(Patient).filter(
        Patient.id == vitals_data.patient_id
    ).first()
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")

    new_vitals = PatientVitals(
        **vitals_data.model_dump(),
        recorded_by=current_user.id
    )
    db.add(new_vitals)
    db.commit()
    db.refresh(new_vitals)

    return VitalsResponse(
        **{c.name: getattr(new_vitals, c.name)
           for c in new_vitals.__table__.columns},
        nurse_name=current_user.full_name
    )

# ─── Get Patient Vitals ───────────────────────────────────
@router.get("/{patient_id}/vitals", response_model=List[VitalsResponse])
def get_patient_vitals(
    patient_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(
        UserRole.admin, UserRole.doctor, UserRole.nurse
    ))
):
    vitals = db.query(PatientVitals).filter(
        PatientVitals.patient_id == patient_id
    ).all()
    result = []
    for v in vitals:
        nurse = db.query(User).filter(User.id == v.recorded_by).first()
        result.append(VitalsResponse(
            **{c.name: getattr(v, c.name) for c in v.__table__.columns},
            nurse_name=nurse.full_name if nurse else None
        ))
    return result