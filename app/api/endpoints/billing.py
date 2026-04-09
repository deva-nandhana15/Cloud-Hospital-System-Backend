from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime, timezone
from app.db.database import get_db
from app.models.models import (
    Billing, Appointment, Patient, Doctor,
    User, UserRole, PaymentStatus, AppointmentStatus,
)
from app.schemas.billing import BillingCreate, BillingUpdate, BillingResponse
from app.api.deps import get_current_active_user, require_role

router = APIRouter()


def build_billing_response(billing, db):
    appointment = db.query(Appointment).filter(
        Appointment.id == billing.appointment_id
    ).first()

    patient = (
        db.query(Patient).filter(Patient.id == appointment.patient_id).first()
        if appointment
        else None
    )

    doctor = (
        db.query(Doctor).filter(Doctor.id == appointment.doctor_id).first()
        if appointment
        else None
    )

    doctor_user = (
        db.query(User).filter(User.id == doctor.user_id).first()
        if doctor
        else None
    )

    return BillingResponse(
        id=billing.id,
        appointment_id=billing.appointment_id,
        consultation_fee=billing.consultation_fee,
        medicine_cost=billing.medicine_cost,
        test_cost=billing.test_cost,
        total_amount=billing.total_amount,
        payment_status=billing.payment_status,
        payment_date=billing.payment_date,
        created_at=billing.created_at,
        patient_name=patient.full_name if patient else None,
        doctor_name=doctor_user.full_name if doctor_user else None,
        appointment_date=appointment.appointment_date if appointment else None,
    )


@router.post("/", response_model=BillingResponse)
def create_bill(
    billing_data: BillingCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_role(UserRole.admin, UserRole.receptionist)
    ),
):
    appointment = db.query(Appointment).filter(
        Appointment.id == billing_data.appointment_id
    ).first()
    if not appointment:
        raise HTTPException(status_code=404, detail="Appointment not found")

    if appointment.status != AppointmentStatus.completed:
        raise HTTPException(
            status_code=400,
            detail="Bill can only be created for completed appointments",
        )

    existing_bill = db.query(Billing).filter(
        Billing.appointment_id == billing_data.appointment_id
    ).first()
    if existing_bill:
        raise HTTPException(
            status_code=400,
            detail="Bill already exists for this appointment",
        )

    total = (
        billing_data.consultation_fee
        + billing_data.medicine_cost
        + billing_data.test_cost
    )

    new_bill = Billing(
        appointment_id=billing_data.appointment_id,
        consultation_fee=billing_data.consultation_fee,
        medicine_cost=billing_data.medicine_cost,
        test_cost=billing_data.test_cost,
        total_amount=total,
        payment_status=PaymentStatus.pending,
        created_by=current_user.id,
    )
    db.add(new_bill)
    db.commit()
    db.refresh(new_bill)

    return build_billing_response(new_bill, db)


@router.get("/", response_model=List[BillingResponse])
def get_all_bills(
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_role(UserRole.admin, UserRole.receptionist, UserRole.doctor)
    ),
):
    bills = db.query(Billing).all()
    return [build_billing_response(b, db) for b in bills]


@router.get("/{bill_id}", response_model=BillingResponse)
def get_bill(
    bill_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_role(
            UserRole.admin, UserRole.receptionist, UserRole.doctor
        )
    ),
):
    bill = db.query(Billing).filter(Billing.id == bill_id).first()
    if not bill:
        raise HTTPException(status_code=404, detail="Bill not found")

    return build_billing_response(bill, db)


@router.put("/{bill_id}", response_model=BillingResponse)
def update_bill(
    bill_id: int,
    billing_data: BillingUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_role(UserRole.admin, UserRole.receptionist)
    ),
):
    bill = db.query(Billing).filter(Billing.id == bill_id).first()
    if not bill:
        raise HTTPException(status_code=404, detail="Bill not found")

    for field, value in billing_data.model_dump(exclude_unset=True).items():
        setattr(bill, field, value)

    bill.total_amount = (
        bill.consultation_fee + bill.medicine_cost + bill.test_cost
    )

    db.commit()
    db.refresh(bill)

    return build_billing_response(bill, db)


@router.patch("/{bill_id}/pay", response_model=BillingResponse)
def mark_as_paid(
    bill_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_role(UserRole.admin, UserRole.receptionist)
    ),
):
    bill = db.query(Billing).filter(Billing.id == bill_id).first()
    if not bill:
        raise HTTPException(status_code=404, detail="Bill not found")

    if bill.payment_status == PaymentStatus.paid:
        raise HTTPException(status_code=400, detail="Bill already paid")

    bill.payment_status = PaymentStatus.paid
    bill.payment_date = datetime.now(timezone.utc)

    db.commit()
    db.refresh(bill)

    return build_billing_response(bill, db)


@router.patch("/{bill_id}/overdue", response_model=BillingResponse)
def mark_as_overdue(
    bill_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.admin)),
):
    bill = db.query(Billing).filter(Billing.id == bill_id).first()
    if not bill:
        raise HTTPException(status_code=404, detail="Bill not found")

    if bill.payment_status == PaymentStatus.paid:
        raise HTTPException(status_code=400, detail="Bill already paid")

    bill.payment_status = PaymentStatus.overdue
    db.commit()
    db.refresh(bill)

    return build_billing_response(bill, db)


@router.delete("/{bill_id}")
def delete_bill(
    bill_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.admin)),
):
    bill = db.query(Billing).filter(Billing.id == bill_id).first()
    if not bill:
        raise HTTPException(status_code=404, detail="Bill not found")
    db.delete(bill)
    db.commit()
    return {"message": "Bill deleted successfully"}
