from sqlalchemy import Column, Integer, String, DateTime, Float, ForeignKey, Enum, Boolean, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.database import Base
import enum

# ─── Enums ────────────────────────────────────────────────
class AppointmentStatus(str, enum.Enum):
    scheduled = "scheduled"
    completed = "completed"
    cancelled = "cancelled"
    no_show = "no_show"

class PaymentStatus(str, enum.Enum):
    pending = "pending"
    paid = "paid"
    overdue = "overdue"

class UserRole(str, enum.Enum):
    admin = "admin"
    doctor = "doctor"
    receptionist = "receptionist"
    nurse = "nurse"

# ─── User Model ───────────────────────────────────────────
class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    full_name = Column(String(100), nullable=False)
    email = Column(String(100), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    role = Column(Enum(UserRole), default=UserRole.receptionist)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

# ─── Patient Model ────────────────────────────────────────
class Patient(Base):
    __tablename__ = "patients"

    id = Column(Integer, primary_key=True, index=True)
    full_name = Column(String(100), nullable=False)
    email = Column(String(100), nullable=True)
    date_of_birth = Column(String(20))
    gender = Column(String(10))
    phone = Column(String(20))
    address = Column(Text)
    blood_group = Column(String(5))
    medical_history = Column(Text)
    registered_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    appointments = relationship("Appointment", back_populates="patient")
    vitals = relationship("PatientVitals", back_populates="patient")

# ─── Doctor Model ─────────────────────────────────────────
class Doctor(Base):
    __tablename__ = "doctors"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    specialization = Column(String(100))
    phone = Column(String(20))
    qualification = Column(String(200))
    experience_years = Column(Integer)
    consultation_fee = Column(Float)
    available_days = Column(String(100))
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User")
    appointments = relationship("Appointment", back_populates="doctor")

# ─── Patient Vitals Model ─────────────────────────────────
class PatientVitals(Base):
    __tablename__ = "patient_vitals"

    id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(Integer, ForeignKey("patients.id"), nullable=False)
    recorded_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    blood_pressure = Column(String(20))
    temperature = Column(Float)
    heart_rate = Column(Integer)
    weight = Column(Float)
    notes = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    patient = relationship("Patient", back_populates="vitals")
    nurse = relationship("User")

# ─── Appointment Model ────────────────────────────────────
class Appointment(Base):
    __tablename__ = "appointments"

    id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(Integer, ForeignKey("patients.id"), nullable=False)
    doctor_id = Column(Integer, ForeignKey("doctors.id"), nullable=False)
    appointment_date = Column(DateTime(timezone=True), nullable=False)
    reason = Column(Text)
    status = Column(Enum(AppointmentStatus), default=AppointmentStatus.scheduled)
    diagnosis = Column(Text, nullable=True)
    prescription = Column(Text, nullable=True)
    lab_test_required = Column(Boolean, default=False)
    notes = Column(Text)
    booked_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    patient = relationship("Patient", back_populates="appointments")
    doctor = relationship("Doctor", back_populates="appointments")
    billing = relationship("Billing", back_populates="appointment", uselist=False)

# ─── Billing Model ────────────────────────────────────────
class Billing(Base):
    __tablename__ = "billing"

    id = Column(Integer, primary_key=True, index=True)
    appointment_id = Column(Integer, ForeignKey("appointments.id"), nullable=False)
    consultation_fee = Column(Float, default=0.0)
    medicine_cost = Column(Float, default=0.0)
    test_cost = Column(Float, default=0.0)
    total_amount = Column(Float, default=0.0)
    payment_status = Column(Enum(PaymentStatus), default=PaymentStatus.pending)
    payment_date = Column(DateTime(timezone=True), nullable=True)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    appointment = relationship("Appointment", back_populates="billing")

# ─── Lab Report Model ─────────────────────────────────────
class LabReport(Base):
    __tablename__ = "lab_reports"

    id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(Integer, ForeignKey("patients.id"), nullable=False)
    appointment_id = Column(Integer, ForeignKey("appointments.id"), nullable=True)
    uploaded_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    file_name = Column(String(255))
    file_path = Column(String(500))
    extracted_data = Column(Text, nullable=True)
    flagged_values = Column(Text, nullable=True)
    status = Column(String(50), default="pending")
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    patient = relationship("Patient")

# ─── Audit Log Model ──────────────────────────────────────
class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    action = Column(String(255))
    details = Column(Text)
    timestamp = Column(DateTime(timezone=True), server_default=func.now())