from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from app.db.database import get_db
from app.models.models import Doctor, User, UserRole
from app.schemas.doctor import DoctorCreate, DoctorUpdate, DoctorResponse
from app.api.deps import get_current_active_user, require_role

router = APIRouter()


@router.post("/", response_model=DoctorResponse)
def create_doctor(
    doctor_data: DoctorCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.admin)),
):
    user = db.query(User).filter(User.id == doctor_data.user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    existing = db.query(Doctor).filter(
        Doctor.user_id == doctor_data.user_id
    ).first()
    if existing:
        raise HTTPException(
            status_code=400, detail="Doctor profile already exists"
        )

    new_doctor = Doctor(**doctor_data.model_dump())
    db.add(new_doctor)
    db.commit()
    db.refresh(new_doctor)

    response = DoctorResponse(
        **{
            c.name: getattr(new_doctor, c.name)
            for c in new_doctor.__table__.columns
        },
        full_name=user.full_name,
        email=user.email,
    )
    return response


@router.get("/", response_model=List[DoctorResponse])
def get_all_doctors(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    doctors = db.query(Doctor).all()
    result = []
    for doctor in doctors:
        user = db.query(User).filter(User.id == doctor.user_id).first()
        response = DoctorResponse(
            **{
                c.name: getattr(doctor, c.name)
                for c in doctor.__table__.columns
            },
            full_name=user.full_name if user else None,
            email=user.email if user else None,
        )
        result.append(response)
    return result


@router.get("/{doctor_id}", response_model=DoctorResponse)
def get_doctor(
    doctor_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    doctor = db.query(Doctor).filter(Doctor.id == doctor_id).first()
    if not doctor:
        raise HTTPException(status_code=404, detail="Doctor not found")

    user = db.query(User).filter(User.id == doctor.user_id).first()
    response = DoctorResponse(
        **{c.name: getattr(doctor, c.name) for c in doctor.__table__.columns},
        full_name=user.full_name if user else None,
        email=user.email if user else None,
    )
    return response


@router.put("/{doctor_id}", response_model=DoctorResponse)
def update_doctor(
    doctor_id: int,
    doctor_data: DoctorUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_role(UserRole.admin, UserRole.doctor)
    ),
):
    doctor = db.query(Doctor).filter(Doctor.id == doctor_id).first()
    if not doctor:
        raise HTTPException(status_code=404, detail="Doctor not found")

    if current_user.role == UserRole.doctor:
        if doctor.user_id != current_user.id:
            raise HTTPException(
                status_code=403,
                detail="You can only update your own doctor profile",
            )

    for field, value in doctor_data.model_dump(exclude_unset=True).items():
        setattr(doctor, field, value)

    db.commit()
    db.refresh(doctor)

    user = db.query(User).filter(User.id == doctor.user_id).first()
    response = DoctorResponse(
        **{c.name: getattr(doctor, c.name) for c in doctor.__table__.columns},
        full_name=user.full_name if user else None,
        email=user.email if user else None,
    )
    return response


@router.delete("/{doctor_id}")
def delete_doctor(
    doctor_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.admin)),
):
    doctor = db.query(Doctor).filter(Doctor.id == doctor_id).first()
    if not doctor:
        raise HTTPException(status_code=404, detail="Doctor not found")
    db.delete(doctor)
    db.commit()
    return {"message": "Doctor deleted successfully"}
