from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field
from src.models.db_models import BedType, BedStatus, PriorityLevel, AppointmentStatus


class MedicineShortagePrediction(BaseModel):
    medicine_name: str
    current_stock: int
    burn_rate_per_day: float
    days_until_stockout: float
    is_shortage_critical: bool

class DecisionEngineResult(BaseModel):
    action_type: str
    priority: PriorityLevel
    bed_allocated: Optional[str] = None
    doctor_assigned: Optional[str] = None
    alerts: List[str] = Field(default_factory=list)
    reasoning: str

class ESIClassification(BaseModel):
    """Rigorous clinical Emergency Severity Index (ESI v4) structure."""
    raw_symptom_analysis: str = Field(
        description="Clinical analysis of the reported symptoms, red flags, and hidden risks in patient phrasing."
    )
    esi_level: int = Field(
        ge=1, le=5,
        description="ESI score: 1=Immediate resuscitation, 2=High risk emergent, 3=Urgent (multiple resources), 4=Semi-urgent (one resource), 5=Non-urgent"
    )
    priority: PriorityLevel = Field(
        description="Normalized hospital priority enum corresponding to ESI."
    )
    recommended_bed: BedType = Field(
        description="Appropriate hospital ward: ICU for ESI 1, EMERGENCY for ESI 2, GENERAL for ESI 3/4."
    )
    recommended_specialty: str = Field(
        description="Medical specialty most qualified for this complaint (e.g., Cardiology, Neurology, Trauma Surgery, Pulmonology, Orthopedics, General Medicine)."
    )
    life_threat_detected: bool = Field(
        description="True if imminent compromise of airway, breathing, circulation, or sudden severe neurological deficit."
    )
    clinical_justification: str = Field(
        description="Formal medical explanation for the triage decision following clinical protocols."
    )
    immediate_orders: List[str] = Field(
        default_factory=list,
        description="Immediate physician orders (e.g. '12-lead ECG stat', 'High-flow O2', 'Trauma Bay Prep', 'IV Access 18G')."
    )


class PatientIntakeAnalysis(BaseModel):
    """Natural language intent parsing across diverse patient phrasings."""
    detected_intent: str = Field(
        description="Must be strictly one of: 'EMERGENCY', 'APPOINTMENT', 'BILLING', 'INVENTORY'"
    )
    confidence: float = Field(
        ge=0.0, le=1.0,
        description="Confidence score for this categorization."
    )
    clinical_urgency_detected: bool = Field(
        description="True if the phrasing implies physical pain, deterioration, distress, or urgent medical evaluation."
    )
    extracted_symptoms: str = Field(
        description="Extracted medical complaints from raw query, standardized into clinical terms."
    )
    direct_response_to_patient: str = Field(
        description="Calm, clear, empathetic message back to the patient or operator."
    )


class DecisionEngineResult(BaseModel):
    action_type: str
    priority: PriorityLevel
    bed_allocated: Optional[str] = None
    doctor_assigned: Optional[str] = None
    alerts: List[str] = Field(default_factory=list)
    reasoning: str