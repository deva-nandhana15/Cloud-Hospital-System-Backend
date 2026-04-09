from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

class PatientCreate(BaseModel):
    full_name: str
    email: Optional[str] = None
    date_of_birth: Optional[str] = None
    gender: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    blood_group: Optional[str] = None
    medical_history: Optional[str] = None

class PatientUpdate(BaseModel):
    full_name: Optional[str] = None
    email: Optional[str] = None
    date_of_birth: Optional[str] = None
    gender: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    blood_group: Optional[str] = None
    medical_history: Optional[str] = None

class VitalsCreate(BaseModel):
    patient_id: int
    blood_pressure: Optional[str] = None
    temperature: Optional[float] = None
    heart_rate: Optional[int] = None
    weight: Optional[float] = None
    notes: Optional[str] = None

class VitalsResponse(BaseModel):
    id: int
    patient_id: int
    recorded_by: int
    blood_pressure: Optional[str] = None
    temperature: Optional[float] = None
    heart_rate: Optional[int] = None
    weight: Optional[float] = None
    notes: Optional[str] = None
    created_at: datetime
    nurse_name: Optional[str] = None

    class Config:
        from_attributes = True

class PatientResponse(BaseModel):
    id: int
    full_name: str
    email: Optional[str] = None
    date_of_birth: Optional[str] = None
    gender: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    blood_group: Optional[str] = None
    medical_history: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True