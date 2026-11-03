from datetime import datetime
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import get_db
from src.orchestrator.workflow import hospital_graph
from src.services.patient_service import PatientService
from src.services.emergency_service import EmergencyService
from src.services.bed_service import BedService
from src.services.doctor_service import DoctorService
from src.services.inventory_service import InventoryService
from src.models.db_models import BedType

router = APIRouter()


# -------------------------------------------------------------
# MAIN AI MULTI-AGENT ORCHESTRATION DISPATCH ENDPOINT
# -------------------------------------------------------------
class OrchestratorRequest(BaseModel):
    name: str = "Anonymous Patient"
    phone: str = "+1-555-0100"
    email: str = "patient@hospital.org"
    age: Optional[int] = 35
    gender: Optional[str] = "Not Specified"
    query: str
    symptoms: Optional[str] = ""
    vitals: Optional[str] = "Normal"
    specialty: Optional[str] = "General Medicine"


@router.post("/dispatch", tags=["0. AI Orchestrator"])
async def dispatch_request(req: OrchestratorRequest, session: AsyncSession = Depends(get_db)):
    """
    Main Multi-Agent Swarm Endpoint:
    1. Resolves patient identity via phone/email (creates new MRN if first visit).
    2. Runs LangGraph Decision Engine across beds, doctors, stock, and triage.
    3. Persists consultation, triage score, and clinical orders in DB.
    4. Returns patient-friendly natural language + clinical trace.
    """
    patient, is_new = await PatientService.get_or_create_patient(
        session=session,
        name=req.name,
        phone=req.phone,
        email=req.email,
        age=req.age or 30,
        gender=req.gender or "Not Specified"
    )

    initial_state = {
        "session": session,
        "patient_id": patient.id,
        "user_query": req.query,
        "symptoms": req.symptoms or req.query,
        "vitals": req.vitals,
        "specialty": req.specialty,
        "intent": "",
        "decision_result": {},
        "agent_output": {},
        "final_response": ""
    }

    result = await hospital_graph.ainvoke(initial_state)

    return {
        "patient_info": {
            "id": patient.id,
            "mrn": patient.mrn,
            "name": patient.name,
            "is_new_patient": is_new,
            "phone": patient.phone,
            "email": patient.email
        },
        "intent_detected": result.get("intent"),
        "decision_engine_evaluation": result.get("decision_result"),
        "patient_friendly_response": result.get("final_response"),
        "clinical_handover": result.get("agent_output", {}).get("details", {}).get("clinical_handover"),
        # Backward compatibility for frontend text rendering:
        "response": result.get("final_response") or result.get("agent_output", {}).get("summary_message") or ""
    }


# -------------------------------------------------------------
# 1. PATIENT SERVICE ENDPOINTS
# -------------------------------------------------------------
class PatientRegisterRequest(BaseModel):
    name: str
    phone: str
    email: str
    age: Optional[int] = 30
    gender: Optional[str] = "Not Specified"


@router.post("/patients/register", tags=["1. Patient Service"])
async def register_or_get_patient(req: PatientRegisterRequest, session: AsyncSession = Depends(get_db)):
    """Resolves identity by Phone/Email. Creates unique MRN if new, returns existing if found."""
    patient, is_new = await PatientService.get_or_create_patient(
        session=session,
        name=req.name,
        phone=req.phone,
        email=req.email,
        age=req.age or 30,
        gender=req.gender or "Not Specified"
    )
    return {
        "status": "created" if is_new else "existing_found",
        "is_new_patient": is_new,
        "patient": {
            "id": patient.id,
            "mrn": patient.mrn,
            "name": patient.name,
            "phone": patient.phone,
            "email": patient.email,
            "priority": patient.priority.value
        }
    }


@router.get("/patients/{identifier}/history", tags=["1. Patient Service"])
async def get_patient_medical_history(identifier: str, session: AsyncSession = Depends(get_db)):
    """
    Retrieves full EHR longitudinal history for a patient by numeric ID or MRN (e.g. 'MRN-2026-INIT01').
    Returns all previous visits, triage scores, orders, appointments, and bills.
    """
    history = await PatientService.get_patient_history(session, identifier)
    if not history:
        raise HTTPException(status_code=404, detail=f"Patient '{identifier}' not found in hospital registry.")
    return history


# -------------------------------------------------------------
# 2. EMERGENCY & CLINICAL TRIAGE ENDPOINTS
# -------------------------------------------------------------
class TriageEvaluationRequest(BaseModel):
    symptoms: str
    vitals: Optional[str] = "Normal"


@router.post("/emergency/triage-eval", tags=["2. Clinical Triage"])
async def evaluate_triage(req: TriageEvaluationRequest):
    """Pure LLM Clinical ESI v4 Evaluation with Chain-of-Thought orders."""
    decision = await EmergencyService.classify_esi(req.symptoms, req.vitals)
    return decision.model_dump()


# -------------------------------------------------------------
# 3. BED MANAGEMENT ENDPOINTS
# -------------------------------------------------------------
class BedAllocateRequest(BaseModel):
    patient_id: int
    bed_type: BedType


@router.get("/beds/breakdown", tags=["3. Bed Service"])
@router.get("/beds/status", tags=["3. Bed Service"])  # Alias for frontend
async def get_bed_breakdown(session: AsyncSession = Depends(get_db)):
    counts = await BedService.get_bed_counts(session)
    return {"beds": counts}


@router.post("/beds/allocate", tags=["3. Bed Service"])
async def allocate_bed(req: BedAllocateRequest, session: AsyncSession = Depends(get_db)):
    """Allocates a specific bed type to a patient. Returns 400 if exhausted."""
    result = await BedService.allocate_bed(session, req.patient_id, req.bed_type)
    if not result.get("success"):
        raise HTTPException(status_code=400, detail=result.get("message"))
    return result


@router.post("/beds/release/{bed_id}", tags=["3. Bed Service"])
async def release_bed(bed_id: int, session: AsyncSession = Depends(get_db)):
    """Marks a bed available upon patient discharge."""
    result = await BedService.release_bed(session, bed_id)
    if not result.get("success"):
        raise HTTPException(status_code=404, detail=result.get("message"))
    return result


# -------------------------------------------------------------
# 4. DOCTOR & SCHEDULING ENDPOINTS
# -------------------------------------------------------------
class ScheduleAppointmentRequest(BaseModel):
    doctor_id: int
    patient_id: int
    start_time: datetime


@router.get("/doctors/roster", tags=["4. Doctor Service"])
@router.get("/doctors/on-duty", tags=["4. Doctor Service"])  # Alias for frontend
async def get_doctors_roster(specialty: Optional[str] = None, session: AsyncSession = Depends(get_db)):
    docs = await DoctorService.get_available_doctors(session, specialty)
    return {"count": len(docs), "doctors": docs}


@router.post("/doctors/schedule", tags=["4. Doctor Service"])
async def schedule_consultation(req: ScheduleAppointmentRequest, session: AsyncSession = Depends(get_db)):
    """Books a physician slot. Fails if there is a scheduling conflict."""
    result = await DoctorService.schedule_appointment(
        session, req.doctor_id, req.patient_id, req.start_time
    )
    if not result.get("success"):
        raise HTTPException(status_code=409, detail=result.get("message"))
    return result


# -------------------------------------------------------------
# 5. PHARMACY INVENTORY PREDICTION ENDPOINTS
# -------------------------------------------------------------
class RestockRequest(BaseModel):
    medicine_name: str
    quantity: int


@router.get("/inventory/predict-shortages", tags=["5. Inventory Service"])
@router.get("/inventory/shortages", tags=["5. Inventory Service"])  # Alias for frontend
async def predict_shortages(threshold_days: float = Query(3.0), session: AsyncSession = Depends(get_db)):
    predictions = await InventoryService.predict_shortages(session, days_threshold=threshold_days)
    return {
        "critical_count": sum(1 for p in predictions if p.is_shortage_critical),
        "predictions": [p.model_dump() for p in predictions]
    }


@router.post("/inventory/restock", tags=["5. Inventory Service"])
async def restock_medicine(req: RestockRequest, session: AsyncSession = Depends(get_db)):
    """Restocks a medicine quantity in the pharmacy database."""
    result = await InventoryService.restock_medicine(session, req.medicine_name, req.quantity)
    if not result.get("success"):
        raise HTTPException(status_code=404, detail=result.get("message"))
    return result