from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field
from src.models.db_models import BedType, BedStatus, PriorityLevel, AppointmentStatus


# Agent Decision Context
class HospitalResourceSnapshot(BaseModel):
    available_beds: dict[BedType, int]
    on_duty_doctors: List[str]
    critical_medicine_shortages: List[str]


# Service Request/Response Models
class BedAssignRequest(BaseModel):
    patient_id: int
    bed_type: BedType


class AppointmentCreate(BaseModel):
    doctor_id: int
    patient_id: int
    start_time: datetime


class MedicineShortagePrediction(BaseModel):
    medicine_name: str
    current_stock: int
    burn_rate_per_day: float
    days_until_stockout: float
    is_shortage_critical: bool


class EmergencyTriageInput(BaseModel):
    patient_id: int
    patient_name: str
    symptoms: str
    vitals: Optional[str] = "Normal"


class DecisionEngineResult(BaseModel):
    action_type: str
    priority: PriorityLevel
    bed_allocated: Optional[str] = None
    doctor_assigned: Optional[str] = None
    alerts: List[str] = Field(default_factory=list)
    reasoning: str