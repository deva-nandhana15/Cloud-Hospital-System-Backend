from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from app.models.models import AppointmentStatus

class AppointmentCreate(BaseModel):
    patient_id: int
    doctor_id: int
    appointment_date: datetime
    reason: Optional[str] = None

class AppointmentUpdate(BaseModel):
    appointment_date: Optional[datetime] = None
    reason: Optional[str] = None
    status: Optional[AppointmentStatus] = None
    notes: Optional[str] = None
    diagnosis: Optional[str] = None
    prescription: Optional[str] = None
    lab_test_required: Optional[bool] = None

class AppointmentResponse(BaseModel):
    id: int
    patient_id: int
    doctor_id: int
    appointment_date: datetime
    reason: Optional[str] = None
    status: AppointmentStatus
    diagnosis: Optional[str] = None
    prescription: Optional[str] = None
    lab_test_required: bool = False
    notes: Optional[str] = None
    created_at: datetime
    patient_name: Optional[str] = None
    doctor_name: Optional[str] = None
    doctor_specialization: Optional[str] = None

    class Config:
        from_attributes = True