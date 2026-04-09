from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from app.models.models import PaymentStatus

class BillingCreate(BaseModel):
    appointment_id: int
    consultation_fee: Optional[float] = 0.0
    medicine_cost: Optional[float] = 0.0
    test_cost: Optional[float] = 0.0

class BillingUpdate(BaseModel):
    consultation_fee: Optional[float] = None
    medicine_cost: Optional[float] = None
    test_cost: Optional[float] = None
    payment_status: Optional[PaymentStatus] = None

class BillingResponse(BaseModel):
    id: int
    appointment_id: int
    consultation_fee: float
    medicine_cost: float
    test_cost: float
    total_amount: float
    payment_status: PaymentStatus
    payment_date: Optional[datetime] = None
    created_at: datetime
    patient_name: Optional[str] = None
    doctor_name: Optional[str] = None
    appointment_date: Optional[datetime] = None

    class Config:
        from_attributes = True