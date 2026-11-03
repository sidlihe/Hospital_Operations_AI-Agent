from datetime import datetime
import enum
import uuid
from sqlalchemy import String, Integer, Float, DateTime, Enum, ForeignKey, Boolean, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from src.core.database import Base


class BedType(str, enum.Enum):
    ICU = "ICU"
    EMERGENCY = "EMERGENCY"
    GENERAL = "GENERAL"
    SURGICAL = "SURGICAL"


class BedStatus(str, enum.Enum):
    AVAILABLE = "AVAILABLE"
    OCCUPIED = "OCCUPIED"
    MAINTENANCE = "MAINTENANCE"


class PriorityLevel(str, enum.Enum):
    LEVEL_1_CRITICAL = "LEVEL_1_CRITICAL"
    LEVEL_2_EMERGENT = "LEVEL_2_EMERGENT"
    LEVEL_3_URGENT = "LEVEL_3_URGENT"
    LEVEL_4_SEMI_URGENT = "LEVEL_4_SEMI_URGENT"
    LEVEL_5_NON_URGENT = "LEVEL_5_NON_URGENT"


class AppointmentStatus(str, enum.Enum):
    SCHEDULED = "SCHEDULED"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"


class EncounterType(str, enum.Enum):
    EMERGENCY_TRIAGE = "EMERGENCY_TRIAGE"
    OUTPATIENT_CONSULT = "OUTPATIENT_CONSULT"
    FOLLOW_UP = "FOLLOW_UP"
    ROUTINE_CHECKUP = "ROUTINE_CHECKUP"


# Doctor entity
class Doctor(Base):
    __tablename__ = "doctors"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    specialty: Mapped[str] = mapped_column(String(100), nullable=False)
    shift_start: Mapped[str] = mapped_column(String(10), default="08:00")
    shift_end: Mapped[str] = mapped_column(String(10), default="17:00")
    is_on_duty: Mapped[bool] = mapped_column(Boolean, default=True)

    appointments = relationship("Appointment", back_populates="doctor")
    consultations = relationship("Consultation", back_populates="doctor")


# Bed allocation entity
class Bed(Base):
    __tablename__ = "beds"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    room_number: Mapped[str] = mapped_column(String(20), nullable=False)
    bed_type: Mapped[BedType] = mapped_column(Enum(BedType), default=BedType.GENERAL)
    status: Mapped[BedStatus] = mapped_column(Enum(BedStatus), default=BedStatus.AVAILABLE)
    assigned_patient_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("patients.id"), nullable=True)

    patient = relationship("Patient", back_populates="bed")


# Medicine Inventory entity
class Medicine(Base):
    __tablename__ = "medicines"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(150), unique=True, nullable=False)
    stock_quantity: Mapped[int] = mapped_column(Integer, default=0)
    burn_rate_per_day: Mapped[float] = mapped_column(Float, default=1.0)
    minimum_threshold: Mapped[int] = mapped_column(Integer, default=20)
    unit_price: Mapped[float] = mapped_column(Float, default=0.0)

    stock_movements = relationship("InventoryTransaction", back_populates="medicine")


class InventoryTransaction(Base):
    __tablename__ = "inventory_transactions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    medicine_id: Mapped[int] = mapped_column(Integer, ForeignKey("medicines.id"), nullable=False)
    quantity_change: Mapped[int] = mapped_column(Integer, nullable=False)
    reason: Mapped[str] = mapped_column(String(200), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    medicine = relationship("Medicine", back_populates="stock_movements")


# Upgraded Patient entity with MRN, Phone, Email
class Patient(Base):
    __tablename__ = "patients"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    mrn: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    age: Mapped[int] = mapped_column(Integer, default=30)
    gender: Mapped[str] = mapped_column(String(10), default="Not Specified")
    phone: Mapped[str] = mapped_column(String(20), unique=True, nullable=False, index=True)
    email: Mapped[str] = mapped_column(String(120), unique=True, nullable=False, index=True)
    priority: Mapped[PriorityLevel] = mapped_column(Enum(PriorityLevel), default=PriorityLevel.LEVEL_5_NON_URGENT)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    bed = relationship("Bed", back_populates="patient", uselist=False)
    appointments = relationship("Appointment", back_populates="patient")
    bills = relationship("Bill", back_populates="patient")
    consultations = relationship("Consultation", back_populates="patient")


# Clinical Consultation / Encounter Entity
class Consultation(Base):
    __tablename__ = "consultations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    patient_id: Mapped[int] = mapped_column(Integer, ForeignKey("patients.id"), nullable=False)
    doctor_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("doctors.id"), nullable=True)
    encounter_type: Mapped[EncounterType] = mapped_column(Enum(EncounterType), default=EncounterType.OUTPATIENT_CONSULT)
    symptoms: Mapped[str] = mapped_column(Text, default="")
    vitals: Mapped[str] = mapped_column(String(150), default="Normal")
    triage_priority: Mapped[PriorityLevel] = mapped_column(Enum(PriorityLevel), default=PriorityLevel.LEVEL_5_NON_URGENT)
    decision_engine_log: Mapped[str] = mapped_column(Text, default="")  # Full JSON string of decision
    patient_friendly_summary: Mapped[str] = mapped_column(Text, default="")
    clinical_orders: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    patient = relationship("Patient", back_populates="consultations")
    doctor = relationship("Doctor", back_populates="consultations")


# Appointment entity
class Appointment(Base):
    __tablename__ = "appointments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    doctor_id: Mapped[int] = mapped_column(Integer, ForeignKey("doctors.id"), nullable=False)
    patient_id: Mapped[int] = mapped_column(Integer, ForeignKey("patients.id"), nullable=False)
    start_time: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    status: Mapped[AppointmentStatus] = mapped_column(Enum(AppointmentStatus), default=AppointmentStatus.SCHEDULED)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    doctor = relationship("Doctor", back_populates="appointments")
    patient = relationship("Patient", back_populates="appointments")


# Billing entity
class Bill(Base):
    __tablename__ = "bills"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    patient_id: Mapped[int] = mapped_column(Integer, ForeignKey("patients.id"), nullable=False)
    total_amount: Mapped[float] = mapped_column(Float, default=0.0)
    is_paid: Mapped[bool] = mapped_column(Boolean, default=False)
    details: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    patient = relationship("Patient", back_populates="bills")