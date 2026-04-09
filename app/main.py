from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.db.database import engine
from app.models import models
from app.api.endpoints import auth, patients, doctors, appointments, billing, lab_reports

models.Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Hospital Management System",
    description="API for Hospital Appointment and Billing",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[*]
    #    "http://localhost:3000","https://polite-pebble-0187fd800.7.azurestaticapps.net"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="/api/auth", tags=["Authentication"])
app.include_router(patients.router, prefix="/api/patients", tags=["Patients"])
app.include_router(doctors.router, prefix="/api/doctors", tags=["Doctors"])
app.include_router(appointments.router, prefix="/api/appointments", tags=["Appointments"])
app.include_router(billing.router, prefix="/api/billing", tags=["Billing"])
app.include_router(lab_reports.router, prefix="/api/lab-reports", tags=["Lab Reports"])

@app.get("/")
def root():
    return {"message": "Hospital Management System API is running!"}