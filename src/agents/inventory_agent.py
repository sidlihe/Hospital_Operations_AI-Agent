from sqlalchemy.ext.asyncio import AsyncSession
from src.agents.base import BaseAgent, AgentResponse
from src.services.inventory_service import InventoryService

INVENTORY_PROMPT = """
You are the Hospital Pharmacy & Inventory Intelligence Agent.
Analyze medicine stock levels and predicted stockout timelines.
Provide an operational warning and prioritized reorder recommendations for hospital procurement.
"""

class InventoryAgent(BaseAgent):
    def __init__(self):
        super().__init__("InventoryAgent", INVENTORY_PROMPT)

    async def audit_stock_and_alert(self, session: AsyncSession) -> AgentResponse:
        predictions = await InventoryService.predict_shortages(session, days_threshold=3.0)
        critical_items = [p for p in predictions if p.is_shortage_critical]

        raw_data = "\n".join([
            f"- {p.medicine_name}: Stock={p.current_stock}, BurnRate={p.burn_rate_per_day}/day, ExhaustionIn={p.days_until_stockout} days"
            for p in predictions
        ])

        ai_summary = await self.execute_prompt(f"Current Stock Audit:\n{raw_data}")

        return AgentResponse(
            agent_name=self.name,
            action_taken="INVENTORY_AUDIT_COMPLETED",
            details={
                "critical_count": len(critical_items),
                "critical_medicines": [c.medicine_name for c in critical_items],
                "all_metrics": [p.model_dump() for p in predictions]
            },
            summary_message=ai_summary
        )