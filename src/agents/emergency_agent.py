from sqlalchemy.ext.asyncio import AsyncSession
from src.agents.base import BaseAgent, AgentResponse
from src.services.emergency_service import EmergencyService
from src.services.bed_service import BedService

EMERGENCY_PROMPT = """
You are the Emergency Triage & Escalation Agent.
Analyze patient urgency based on the ESI classification provided.
Formulate a decisive hospital escalation message specifying required triage team, bed reservation urgency, and priority level.
"""

class EmergencyAgent(BaseAgent):
    def __init__(self):
        super().__init__("EmergencyAgent", EMERGENCY_PROMPT)

    async def triage_and_admit(
        self,
        session: AsyncSession,
        patient_id: int,
        symptoms: str,
        vitals: str = "Normal"
    ) -> AgentResponse:
        triage_info = EmergencyService.classify_esi(symptoms, vitals)
        bed_alloc = await BedService.allocate_bed(
            session=session,
            patient_id=patient_id,
            bed_type=triage_info["recommended_bed"]
        )

        prompt_input = (
            f"Patient {patient_id} triage: Priority {triage_info['priority'].value}, "
            f"Recommended Bed: {triage_info['recommended_bed'].value}, Action: {triage_info['immediate_action']}, "
            f"Bed Allocation Status: {bed_alloc}"
        )
        ai_summary = await self.execute_prompt(prompt_input)

        return AgentResponse(
            agent_name=self.name,
            action_taken="EMERGENCY_TRIAGE_EVALUATED",
            details={
                "priority": triage_info["priority"].value,
                "bed_allocation": bed_alloc,
                "immediate_action": triage_info["immediate_action"]
            },
            summary_message=ai_summary
        )