from sqlalchemy.ext.asyncio import AsyncSession
from src.core.logger import logger
from src.models.schemas import DecisionEngineResult, ESIClassification
from src.models.db_models import PriorityLevel, BedType
from src.services.bed_service import BedService
from src.services.doctor_service import DoctorService
from src.services.inventory_service import InventoryService
from src.services.emergency_service import EmergencyService


class DecisionEngine:
    @staticmethod
    async def evaluate_admission_or_intake(
        session: AsyncSession,
        symptoms: str,
        vitals: str = "Normal"
    ) -> DecisionEngineResult:
        logger.info(f"[DecisionEngine] Beginning multi-factor evaluation for symptoms='{symptoms}'")
        alerts: list[str] = []

        # 1. Autonomous Clinical ESI Evaluation
        triage: ESIClassification = await EmergencyService.classify_esi(symptoms, vitals)
        priority: PriorityLevel = triage.priority
        recommended_bed: BedType = triage.recommended_bed
        target_specialty: str = triage.recommended_specialty

        # 2. Resource Availability: Beds
        bed_counts = await BedService.get_bed_counts(session)
        available_target_beds = bed_counts.get(f"{recommended_bed.value}_AVAILABLE", 0)

        # 3. Resource Availability: Critical Medications
        shortages = await InventoryService.predict_shortages(session)
        critical_shortages = [s.medicine_name for s in shortages if s.is_shortage_critical]
        if critical_shortages:
            alerts.append(f"PHARMACY ALERT: Critical exhaustion expected for: {', '.join(critical_shortages)}")

        # 4. Physician Availability Matching
        available_docs = await DoctorService.get_available_doctors(session, specialty=target_specialty)
        assigned_doctor = available_docs[0]["name"] if available_docs else None

        if not assigned_doctor:
            alerts.append(f"ROSTER GAP: No on-duty specialist for {target_specialty}. Diverting to General Emergency staff.")
            all_docs = await DoctorService.get_available_doctors(session)
            assigned_doctor = all_docs[0]["name"] if all_docs else "Emergency Response Team (On-Call)"

        # 5. Formulate Decision Strategy Based on ESI Level
        if triage.esi_level in [1, 2]:
            action_type = "STAT_EMERGENCY_ADMISSION"
            if available_target_beds == 0:
                alerts.append(f"SURGE CAPACITY PROTOCOL: Zero {recommended_bed.value} beds available! Escalating to overflow.")
                bed_decision = f"CRITICAL OVERFLOW: No {recommended_bed.value} available. Diverted to Surge / Holding Bay."
            else:
                bed_decision = f"Immediate reservation of {recommended_bed.value} Bed (Available: {available_target_beds})"

            reasoning = (
                f"[ESI Level {triage.esi_level} - {priority.value}] {triage.clinical_justification} "
                f"Stat orders: {', '.join(triage.immediate_orders)}. Lead Attending: {assigned_doctor}."
            )

        elif triage.esi_level == 3:
            action_type = "URGENT_INPATIENT_OBSERVATION"
            if available_target_beds == 0:
                bed_decision = "General beds at capacity. Queueing in urgent holding."
                alerts.append("BED DELAY: General ward full. Patient queued in observation bay.")
            else:
                bed_decision = f"General Inpatient Bed Reserved (Available: {available_target_beds})"

            reasoning = (
                f"[ESI Level 3 - Urgent] Requires multi-resource diagnostic workup ({', '.join(triage.immediate_orders)}). "
                f"Physician Assigned: {assigned_doctor}."
            )

        else:
            action_type = "OUTPATIENT_CLINICAL_CONSULT"
            bed_decision = "No Inpatient Bed Required (Ambulatory / Outpatient Care)"
            reasoning = (
                f"[ESI Level {triage.esi_level} - Low Acuity] {triage.clinical_justification} "
                f"Referred to {assigned_doctor} for standard consultation."
            )

        logger.info(f"[DecisionEngine] Decision finalized: Action={action_type} | Staff={assigned_doctor}")

        return DecisionEngineResult(
            action_type=action_type,
            priority=priority,
            bed_allocated=bed_decision,
            doctor_assigned=assigned_doctor,
            alerts=alerts,
            reasoning=reasoning
        )