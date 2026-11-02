from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from src.agents.base import BaseAgent, AgentResponse
from src.services.doctor_service import DoctorService

APPOINTMENT_PROMPT = """
You are the Hospital Appointment Agent.
Your job is to match patient consultation requests to the best available physician based on specialty, shifts, and schedules.
Provide a clear, patient-friendly confirmation and schedule summary.
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
        doctors = await DoctorService.get_available_doctors(session, specialty=specialty)
        
        if not doctors:
            # Fallback to any on-duty doctor
            doctors = await DoctorService.get_available_doctors(session)

        if not doctors:
            return AgentResponse(
                agent_name=self.name,
                status="failed",
                action_taken="NO_DOCTOR_AVAILABLE",
                details={},
                summary_message="No physicians currently on duty matching requirements."
            )

        selected_doctor = doctors[0]
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

        ai_summary = await self.execute_prompt(
            f"Scheduled patient {patient_id} with {selected_doctor['name']} ({selected_doctor['specialty']}) at {preferred_time.isoformat()}."
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
            summary_message=ai_summary
        )