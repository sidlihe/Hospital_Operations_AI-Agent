from datetime import datetime
import enum
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
    LEVEL_1_CRITICAL = "LEVEL_1_CRITICAL"   # Resuscitation needed (immediate)
    LEVEL_2_EMERGENT = "LEVEL_2_EMERGENT"   # Emergent (minutes)
    LEVEL_3_URGENT = "LEVEL_3_URGENT"       # Urgent (under an hour)
    LEVEL_4_SEMI_URGENT = "LEVEL_4_SEMI_URGENT"
    LEVEL_5_NON_URGENT = "LEVEL_5_NON_URGENT"


class AppointmentStatus(str, enum.Enum):
    SCHEDULED = "SCHEDULED"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"


# Doctor entity
class Doctor(Base):
    __tablename__ = "doctors"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    specialty: Mapped[str] = mapped_column(String(100), nullable=False)
    shift_start: Mapped[str] = mapped_column(String(10), default="08:00")  # HH:MM
    shift_end: Mapped[str] = mapped_column(String(10), default="17:00")
    is_on_duty: Mapped[bool] = mapped_column(Boolean, default=True)

    appointments = relationship("Appointment", back_populates="doctor")


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


# Patient entity
class Patient(Base):
    __tablename__ = "patients"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    age: Mapped[int] = mapped_column(Integer, nullable=False)
    priority: Mapped[PriorityLevel] = mapped_column(Enum(PriorityLevel), default=PriorityLevel.LEVEL_5_NON_URGENT)
    symptoms: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    bed = relationship("Bed", back_populates="patient", uselist=False)
    appointments = relationship("Appointment", back_populates="patient")
    bills = relationship("Bill", back_populates="patient")


# Appointment entity
class Appointment(Base):
    __tablename__ = "appointments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    doctor_id: Mapped[int] = mapped_column(Integer, ForeignKey("doctors.id"), nullable=False)
    patient_id: Mapped[int] = mapped_column(Integer, ForeignKey("patients.id"), nullable=False)
    start_time: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    status: Mapped[AppointmentStatus] = mapped_column(Enum(AppointmentStatus), default=AppointmentStatus.SCHEDULED)

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