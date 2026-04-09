from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class DoctorCreate(BaseModel):
    user_id: int
    specialization: Optional[str] = None
    phone: Optional[str] = None
    qualification: Optional[str] = None
    experience_years: Optional[int] = None
    consultation_fee: Optional[float] = None
    available_days: Optional[str] = None

class DoctorUpdate(BaseModel):
    specialization: Optional[str] = None
    phone: Optional[str] = None
    qualification: Optional[str] = None
    experience_years: Optional[int] = None
    consultation_fee: Optional[float] = None
    available_days: Optional[str] = None

class DoctorResponse(BaseModel):
    id: int
    user_id: int
    specialization: Optional[str] = None
    phone: Optional[str] = None
    qualification: Optional[str] = None
    experience_years: Optional[int] = None
    consultation_fee: Optional[float] = None
    available_days: Optional[str] = None
    created_at: datetime
    full_name: Optional[str] = None
    email: Optional[str] = None

    class Config:
        from_attributes = True