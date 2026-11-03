import json
from sqlalchemy.ext.asyncio import AsyncSession
from src.agents.base import BaseAgent, AgentResponse
from src.services.emergency_service import EmergencyService
from src.services.bed_service import BedService
from src.services.patient_service import PatientService
from src.models.db_models import EncounterType
from src.core.logger import logger
from src.models.schemas import ESIClassification

EMERGENCY_DUAL_PROMPT = """
You are the Emergency Department Lead Clinical Coordinator.
Generate two distinct responses in strict JSON format:
1. "patient_friendly_message": A calm, clear, jargon-free explanation to the patient and their family describing what is happening, why they are being prioritized, and what our team is doing right now to take care of them.
2. "clinical_handover_note": A concise, formal clinical summary with immediate orders, expected bed transfer, and assigned attending doctor.

Output JSON format strictly:
{
  "patient_friendly_message": "...",
  "clinical_handover_note": "..."
}
"""

class EmergencyAgent(BaseAgent):
    def __init__(self):
        super().__init__("EmergencyAgent", EMERGENCY_DUAL_PROMPT)

    async def triage_and_admit(
        self,
        session: AsyncSession,
        patient_id: int,
        symptoms: str,
        vitals: str = "Normal",
        doctor_id: int | None = None
    ) -> AgentResponse:
        logger.info(f"[EmergencyAgent] Triage & admit for patient_id={patient_id}")
        triage: ESIClassification = await EmergencyService.classify_esi(symptoms, vitals)

        bed_alloc = None
        if triage.esi_level <= 3:
            bed_alloc = await BedService.allocate_bed(
                session=session,
                patient_id=patient_id,
                bed_type=triage.recommended_bed
            )

        prompt_input = (
            f"Patient ID: {patient_id}\n"
            f"ESI Level: {triage.esi_level} ({triage.priority.value})\n"
            f"Symptoms: {symptoms}\n"
            f"Vitals: {vitals}\n"
            f"Diagnosis Context: {triage.clinical_justification}\n"
            f"Immediate Orders: {', '.join(triage.immediate_orders)}\n"
            f"Bed Allocation Status: {bed_alloc if bed_alloc else 'Outpatient - No Inpatient Bed Required'}\n"
        )

        raw_output = await self.execute_prompt(prompt_input)
        
        # Parse dual format
        try:
            cleaned = raw_output.replace("```json", "").replace("```", "").strip()
            parsed = json.loads(cleaned)
            patient_msg = parsed.get("patient_friendly_message", raw_output)
            clinical_note = parsed.get("clinical_handover_note", raw_output)
        except Exception:
            patient_msg = (
                f"Your symptoms have been triaged as priority {triage.priority.value}. "
                f"Our clinical team has reserved appropriate care and a physician is attending to you immediately."
            )
            clinical_note = raw_output

        # Save to database Consultations table
        await PatientService.record_consultation(
            session=session,
            patient_id=patient_id,
            doctor_id=doctor_id,
            encounter_type=EncounterType.EMERGENCY_TRIAGE,
            symptoms=symptoms,
            vitals=vitals,
            triage_priority=triage.priority,
            decision_log=json.dumps(triage.model_dump(), default=str),
            patient_summary=patient_msg,
            orders=", ".join(triage.immediate_orders)
        )

        return AgentResponse(
            agent_name=self.name,
            action_taken="EMERGENCY_TRIAGE_EVALUATED",
            details={
                "esi_level": triage.esi_level,
                "priority": triage.priority.value,
                "recommended_bed": triage.recommended_bed.value,
                "bed_allocation": bed_alloc,
                "immediate_orders": triage.immediate_orders,
                "clinical_handover": clinical_note
            },
            summary_message=patient_msg
        )