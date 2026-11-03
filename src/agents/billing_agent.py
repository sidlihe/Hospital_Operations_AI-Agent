from sqlalchemy.ext.asyncio import AsyncSession
from src.agents.base import BaseAgent, AgentResponse
from src.models.db_models import Bill
from src.core.logger import logger

BILLING_PROMPT = """
You are the Hospital Billing & Finance Officer.
Format an itemized statement breakdown clearly:
- Itemized charges (Ward, Clinical Consult, Diagnostics/Meds)
- Insurance coverage adjustment (80% for insured patients)
- Out-of-pocket balance due
- Payment instructions
Be transparent, professional, and courteous.
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
        logger.info(f"[BillingAgent] Generating bill for patient_id={patient_id}, bed_type='{bed_type}'")

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

        # Persist to database
        bill = Bill(
            patient_id=patient_id,
            total_amount=patient_copay,
            is_paid=False,
            details=f"Ward ({bed_type} x {bed_days}d): ${room_charge:.2f}, Consult: ${consultation_charge:.2f}, Pharmacy: ${medication_base:.2f}. Ins covered: ${insurance_covered:.2f}"
        )
        session.add(bill)
        await session.commit()
        await session.refresh(bill)

        summary = await self.execute_prompt(
            f"Invoice #{bill.id}: Room ({bed_type} x {bed_days} days) = ${room_charge}, "
            f"Physician Consult = ${consultation_charge}, Pharmacy/Supplies = ${medication_base}. "
            f"Gross Total = ${gross_total}. Insurance Applied (80%) = ${insurance_covered}. "
            f"Patient Responsibility = ${patient_copay}."
        )

        return AgentResponse(
            agent_name=self.name,
            action_taken="BILL_GENERATED",
            details={
                "bill_id": bill.id,
                "gross_total": gross_total,
                "insurance_covered": insurance_covered,
                "patient_copay": patient_copay
            },
            summary_message=summary
        )