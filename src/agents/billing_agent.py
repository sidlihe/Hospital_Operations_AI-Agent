from sqlalchemy.ext.asyncio import AsyncSession
from src.agents.base import BaseAgent, AgentResponse
from src.models.db_models import Bill
from src.core.logger import get_logger

logger = get_logger(__name__)

BILLING_PROMPT = """
You are the Hospital Billing & Finance Agent.
Format the hospital bill clearly, indicating service charges, insurance adjustment estimates (default 80% coverage for insured patients), and patient out-of-pocket balance.
"""

class BillingAgent(BaseAgent):
    def __init__(self):
        super().__init__("BillingAgent", BILLING_PROMPT)

    async def generate_bill(
        self,
        session: AsyncSession,
        patient_id: int,
        bed_days: int = 1,
        bed_type: str = "GENERAL",
        has_insurance: bool = True
    ) -> AgentResponse:
        # Standard rate card
        rate_card = {
            "ICU": 1500.0,
            "EMERGENCY": 800.0,
            "GENERAL": 300.0,
            "SURGICAL": 1200.0
        }
        
        base_rate = rate_card.get(bed_type.upper(), 300.0)
        room_charge = base_rate * bed_days
        consultation_charge = 150.0
        medication_base = 120.0
        gross_total = room_charge + consultation_charge + medication_base

        insurance_covered = (gross_total * 0.8) if has_insurance else 0.0
        patient_copay = gross_total - insurance_covered

        # Persist bill
        bill = Bill(
            patient_id=patient_id,
            total_amount=patient_copay,
            is_paid=False,
            details=f"Bed ({bed_type} x {bed_days}d): ${room_charge}, Consult: ${consultation_charge}, Meds: ${medication_base}. Insurance covered: ${insurance_covered}"
        )
        session.add(bill)
        await session.commit()
        await session.refresh(bill)
        logger.info("Bill generated")

        prompt_input = (
            f"Gross Total: ${gross_total}, Insurance Coverage: ${insurance_covered}, "
            f"Patient Responsibility: ${patient_copay}, Bill ID: {bill.id}."
        )
        ai_summary = await self.execute_prompt(prompt_input)

        return AgentResponse(
            agent_name=self.name,
            action_taken="BILL_GENERATED",
            details={
                "bill_id": bill.id,
                "gross_total": gross_total,
                "insurance_covered": insurance_covered,
                "patient_copay": patient_copay
            },
            summary_message=ai_summary
        )