from langchain_core.prompts import ChatPromptTemplate
from src.core.llm import get_llm
from src.core.logger import logger
from src.models.schemas import PatientIntakeAnalysis

INTAKE_SYSTEM_PROMPT = """
You are the Chief Hospital Intake Officer.
Patients and staff submit queries in unstructured natural language.
Analyze the request and classify into:
1. 'EMERGENCY': Any physical symptom, trauma, injury, sudden pain, distress, or medical deterioration.
2. 'APPOINTMENT': Routine scheduling, rescheduling, checkup requests, or non-acute specialist consults.
3. 'BILLING': Questions about payment, cost estimates, invoices, insurance verification, receipts.
4. 'INVENTORY': Inquiries about drug stock, shortages, or pharmacy availability.

CRITICAL SAFETY DIRECTIVE:
If the user mentions ANY physical discomfort, acute symptom, or potential health crisis (even casually, e.g., 'my neck hurts a bit after the crash'), ALWAYS classify as 'EMERGENCY' to ensure medical triage runs first.
"""

class PatientAgent:
    def __init__(self):
        self.llm = get_llm(temperature=0.0)
        self.structured_llm = self.llm.with_structured_output(PatientIntakeAnalysis)
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", INTAKE_SYSTEM_PROMPT),
            ("human", "Raw User Query:\n{user_query}")
        ])

    async def parse_intent(self, user_query: str) -> PatientIntakeAnalysis:
        logger.info(f"[PatientAgent] Parsing raw query: '{user_query}'")
        chain = self.prompt | self.structured_llm

        try:
            analysis: PatientIntakeAnalysis = await chain.ainvoke({"user_query": user_query})
            logger.info(
                f"[PatientAgent] Result: Intent={analysis.detected_intent} | "
                f"Urgency={analysis.clinical_urgency_detected} | Confidence={analysis.confidence}"
            )
            return analysis
        except Exception as e:
            logger.error(f"[PatientAgent] Failed to parse intent: {e}", exc_info=True)
            return PatientIntakeAnalysis(
                detected_intent="EMERGENCY",
                confidence=0.5,
                clinical_urgency_detected=True,
                extracted_symptoms=user_query,
                direct_response_to_patient="We are routing your request immediately to emergency medical evaluation."
            )