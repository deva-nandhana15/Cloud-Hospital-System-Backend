from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from app.db.database import get_db
from app.models.models import (
    Appointment,
    Patient,
    Doctor,
    User,
    UserRole,
    AppointmentStatus,
)
from app.schemas.appointment import (
    AppointmentCreate,
    AppointmentUpdate,
    AppointmentResponse,
)
from app.api.deps import get_current_active_user, require_role

router = APIRouter()


def build_appointment_response(appointment, db):
    patient = db.query(Patient).filter(
        Patient.id == appointment.patient_id
    ).first()
    doctor = db.query(Doctor).filter(
        Doctor.id == appointment.doctor_id
    ).first()
    doctor_user = (
        db.query(User).filter(User.id == doctor.user_id).first()
        if doctor
        else None
    )

    return AppointmentResponse(
        id=appointment.id,
        patient_id=appointment.patient_id,
        doctor_id=appointment.doctor_id,
        appointment_date=appointment.appointment_date,
        reason=appointment.reason,
        status=appointment.status,
        diagnosis=appointment.diagnosis,
        prescription=appointment.prescription,
        lab_test_required=appointment.lab_test_required or False,
        notes=appointment.notes,
        created_at=appointment.created_at,
        patient_name=patient.full_name if patient else None,
        doctor_name=doctor_user.full_name if doctor_user else None,
        doctor_specialization=doctor.specialization if doctor else None,
    )


def _doctor_record_for_user(db: Session, user: User):
    return db.query(Doctor).filter(Doctor.user_id == user.id).first()


@router.post("/", response_model=AppointmentResponse)
def book_appointment(
    appointment_data: AppointmentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_role(UserRole.admin, UserRole.receptionist)
    ),
):
    patient = db.query(Patient).filter(
        Patient.id == appointment_data.patient_id
    ).first()
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")

    doctor = db.query(Doctor).filter(
        Doctor.id == appointment_data.doctor_id
    ).first()
    if not doctor:
        raise HTTPException(status_code=404, detail="Doctor not found")

    new_appointment = Appointment(
        patient_id=appointment_data.patient_id,
        doctor_id=appointment_data.doctor_id,
        appointment_date=appointment_data.appointment_date,
        reason=appointment_data.reason,
        status=AppointmentStatus.scheduled,
        booked_by=current_user.id,
    )
    db.add(new_appointment)
    db.commit()
    db.refresh(new_appointment)
    return build_appointment_response(new_appointment, db)


@router.get("/", response_model=List[AppointmentResponse])
def get_all_appointments(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    if current_user.role == UserRole.doctor:
        doctor = _doctor_record_for_user(db, current_user)
        if not doctor:
            return []
        appointments = db.query(Appointment).filter(
            Appointment.doctor_id == doctor.id
        ).all()
    else:
        appointments = db.query(Appointment).all()

    return [build_appointment_response(a, db) for a in appointments]


@router.get("/{appointment_id}", response_model=AppointmentResponse)
def get_appointment(
    appointment_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    appointment = db.query(Appointment).filter(
        Appointment.id == appointment_id
    ).first()
    if not appointment:
        raise HTTPException(status_code=404, detail="Appointment not found")

    if current_user.role == UserRole.doctor:
        doctor = _doctor_record_for_user(db, current_user)
        if not doctor or appointment.doctor_id != doctor.id:
            raise HTTPException(status_code=403, detail="Not authorized")

    return build_appointment_response(appointment, db)


@router.put("/{appointment_id}", response_model=AppointmentResponse)
def update_appointment(
    appointment_id: int,
    appointment_data: AppointmentUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    appointment = db.query(Appointment).filter(
        Appointment.id == appointment_id
    ).first()
    if not appointment:
        raise HTTPException(status_code=404, detail="Appointment not found")

    if current_user.role == UserRole.nurse:
        raise HTTPException(
            status_code=403, detail="Nurses cannot modify appointments"
        )

    data = appointment_data.model_dump(exclude_unset=True)

    if current_user.role == UserRole.doctor:
        doctor = _doctor_record_for_user(db, current_user)
        if not doctor or appointment.doctor_id != doctor.id:
            raise HTTPException(status_code=403, detail="Not authorized")
        allowed = {
            "diagnosis",
            "prescription",
            "notes",
            "lab_test_required",
            "status",
        }
        for field, value in data.items():
            if field in allowed:
                setattr(appointment, field, value)

    elif current_user.role == UserRole.receptionist:
        allowed = {"appointment_date", "reason"}
        for field, value in data.items():
            if field in allowed:
                setattr(appointment, field, value)

    else:
        for field, value in data.items():
            setattr(appointment, field, value)

    db.commit()
    db.refresh(appointment)
    return build_appointment_response(appointment, db)


@router.patch(
    "/{appointment_id}/complete",
    response_model=AppointmentResponse,
)
def complete_appointment(
    appointment_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_role(
            UserRole.doctor,
            UserRole.admin,
            UserRole.receptionist,
        )
    ),
):
    appointment = db.query(Appointment).filter(
        Appointment.id == appointment_id
    ).first()
    if not appointment:
        raise HTTPException(status_code=404, detail="Appointment not found")

    if current_user.role == UserRole.doctor:
        doctor = _doctor_record_for_user(db, current_user)
        if not doctor or appointment.doctor_id != doctor.id:
            raise HTTPException(status_code=403, detail="Not authorized")

    appointment.status = AppointmentStatus.completed
    db.commit()
    db.refresh(appointment)
    return build_appointment_response(appointment, db)


@router.patch(
    "/{appointment_id}/cancel",
    response_model=AppointmentResponse,
)
def cancel_appointment(
    appointment_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_role(UserRole.admin, UserRole.receptionist)
    ),
):
    appointment = db.query(Appointment).filter(
        Appointment.id == appointment_id
    ).first()
    if not appointment:
        raise HTTPException(status_code=404, detail="Appointment not found")
    if appointment.status == AppointmentStatus.cancelled:
        raise HTTPException(status_code=400, detail="Already cancelled")
    appointment.status = AppointmentStatus.cancelled
    db.commit()
    db.refresh(appointment)
    return build_appointment_response(appointment, db)


@router.delete("/{appointment_id}")
def delete_appointment(
    appointment_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.admin)),
):
    appointment = db.query(Appointment).filter(
        Appointment.id == appointment_id
    ).first()
    if not appointment:
        raise HTTPException(status_code=404, detail="Appointment not found")
    db.delete(appointment)
    db.commit()
    return {"message": "Appointment deleted successfully"}