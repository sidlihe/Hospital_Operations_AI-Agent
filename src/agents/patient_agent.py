from src.agents.base import BaseAgent, AgentResponse
from src.core.logger import get_logger

logger = get_logger(__name__)

PATIENT_INTAKE_PROMPT = """
You are the Patient Intake & Front-Desk Agent.
Analyze the user's intent. Categorize into exactly one target:
- 'EMERGENCY' (severe pain, injury, trauma, shortness of breath, unconsciousness)
- 'APPOINTMENT' (routine visits, checkups, booking, doctor consultations)
- 'BILLING' (invoices, costs, insurance, payments)
- 'INVENTORY' (medicine availability inquiries)

Respond in this JSON format strictly:
{
  "target": "EMERGENCY" | "APPOINTMENT" | "BILLING" | "INVENTORY",
  "reasoning": "short explanation",
  "patient_message": "helpful message back to the patient"
}
"""

class PatientAgent(BaseAgent):
    def __init__(self):
        super().__init__("PatientAgent", PATIENT_INTAKE_PROMPT)

    async def parse_intent(self, user_query: str) -> dict:
        import json
        raw = await self.execute_prompt(f"Patient Request: {user_query}")
        try:
            # Clean markdown if enclosed in ```json
            cleaned = raw.replace("```json", "").replace("```", "").strip()
            return json.loads(cleaned)
        except json.JSONDecodeError:
            # Safe fallback
            logger.warning("Patient intent response was not valid JSON; using fallback")
            return {
                "target": "APPOINTMENT",
                "reasoning": "Defaulting due to parsing fallback",
                "patient_message": raw
            }