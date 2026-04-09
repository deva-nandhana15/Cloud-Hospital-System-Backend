from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class LabReportResponse(BaseModel):
    id: int
    patient_id: int
    appointment_id: Optional[int] = None
    uploaded_by: int
    file_name: Optional[str] = None
    extracted_data: Optional[str] = None
    flagged_values: Optional[str] = None
    status: str
    created_at: datetime
    patient_name: Optional[str] = None

    class Config:
        from_attributes = True