from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from src.agents.base import BaseAgent, AgentResponse
from src.services.doctor_service import DoctorService
from src.services.patient_service import PatientService
from src.models.db_models import EncounterType, PriorityLevel
from src.core.logger import logger

APPOINTMENT_PROMPT = """
You are the Hospital Appointment Coordinator.
Generate a clear, polite, and reassuring appointment confirmation message for the patient.
Include the doctor's name, specialty, confirmed date/time, and pre-visit instructions (e.g. arrive 15 minutes early, bring previous medical records).
"""

class AppointmentAgent(BaseAgent):
    def __init__(self):
        super().__init__("AppointmentAgent", APPOINTMENT_PROMPT)

    async def book_appointment(
        self,
        session: AsyncSession,
        patient_id: int,
        specialty: str,
        preferred_time: datetime
    ) -> AgentResponse:
        logger.info(f"[AppointmentAgent] Booking request for patient_id={patient_id}, specialty='{specialty}'")
        
        # 1. Match physician by specialty
        doctors = await DoctorService.get_available_doctors(session, specialty=specialty)
        if not doctors:
            doctors = await DoctorService.get_available_doctors(session)

        if not doctors:
            return AgentResponse(
                agent_name=self.name,
                status="failed",
                action_taken="NO_DOCTOR_AVAILABLE",
                details={},
                summary_message="Currently no physicians available on duty for the requested department."
            )

        selected_doctor = doctors[0]
        
        # 2. Book appointment slot
        booking = await DoctorService.schedule_appointment(
            session=session,
            doctor_id=selected_doctor["id"],
            patient_id=patient_id,
            start_time=preferred_time
        )

        if not booking["success"]:
            return AgentResponse(
                agent_name=self.name,
                status="conflict",
                action_taken="SLOT_CONFLICT",
                details=booking,
                summary_message=booking["message"]
            )

        # 3. Generate patient-friendly confirmation
        summary = await self.execute_prompt(
            f"Doctor: {selected_doctor['name']} ({selected_doctor['specialty']})\n"
            f"Scheduled Time: {preferred_time.strftime('%A, %B %d, %Y at %I:%M %p')}\n"
            f"Appointment Reference: #{booking['appointment_id']}"
        )

        # 4. Save to consultations table as an encounter
        await PatientService.record_consultation(
            session=session,
            patient_id=patient_id,
            doctor_id=selected_doctor["id"],
            encounter_type=EncounterType.OUTPATIENT_CONSULT,
            symptoms="Scheduled Outpatient Consultation",
            vitals="Pending at Check-in",
            triage_priority=PriorityLevel.LEVEL_5_NON_URGENT,
            decision_log=f"Booked appointment with {selected_doctor['name']}",
            patient_summary=summary,
            orders=f"Consultation scheduled for {preferred_time.isoformat()}"
        )

        return AgentResponse(
            agent_name=self.name,
            action_taken="APPOINTMENT_SCHEDULED",
            details={
                "appointment_id": booking["appointment_id"],
                "doctor": selected_doctor["name"],
                "specialty": selected_doctor["specialty"],
                "start_time": preferred_time.isoformat()
            },
            summary_message=summary
        )