from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from src.models.db_models import Medicine
from src.models.schemas import MedicineShortagePrediction

class InventoryService:
    @staticmethod
    async def predict_shortages(session: AsyncSession, days_threshold: float = 3.0) -> list[MedicineShortagePrediction]:
        result = await session.execute(select(Medicine))
        medicines = result.scalars().all()

        predictions = []
        for med in medicines:
            burn_rate = med.burn_rate_per_day if med.burn_rate_per_day > 0 else 0.1
            days_left = round(med.stock_quantity / burn_rate, 1)
            
            # Critical if remaining supply is below threshold or stock <= minimum threshold
            is_critical = (days_left <= days_threshold) or (med.stock_quantity <= med.minimum_threshold)
            
            predictions.append(
                MedicineShortagePrediction(
                    medicine_name=med.name,
                    current_stock=med.stock_quantity,
                    burn_rate_per_day=med.burn_rate_per_day,
                    days_until_stockout=days_left,
                    is_shortage_critical=is_critical
                )
            )
        return predictions

    @staticmethod
    async def restock_medicine(session: AsyncSession, medicine_name: str, quantity: int) -> dict:
        query = select(Medicine).where(Medicine.name.ilike(medicine_name))
        med = (await session.execute(query)).scalar_one_or_none()
        
        if not med:
            return {"success": False, "message": f"Medicine {medicine_name} not found"}

        med.stock_quantity += quantity
        await session.commit()
        await session.refresh(med)
        return {
            "success": True,
            "medicine": med.name,
            "new_stock": med.stock_quantity
        }