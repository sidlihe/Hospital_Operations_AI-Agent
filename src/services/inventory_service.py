from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from src.models.db_models import InventoryTransaction, Medicine
from src.models.schemas import MedicineShortagePrediction
from src.core.logger import logger

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
        critical_count = sum(prediction.is_shortage_critical for prediction in predictions)
        if critical_count:
            logger.warning("Inventory forecast found %d critical shortage(s)", critical_count)
        return predictions

    @staticmethod
    async def adjust_stock(
        session: AsyncSession,
        medicine_name: str,
        quantity_change: int,
        reason: str,
    ) -> dict:
        normalized_reason = reason.strip()
        if not normalized_reason:
            return {"success": False, "message": "A stock adjustment reason is required."}

        query = select(Medicine).where(Medicine.name.ilike(medicine_name))
        med = (await session.execute(query)).scalar_one_or_none()
        
        if not med:
            logger.warning("Medicine stock adjustment failed: item not found")
            return {"success": False, "message": f"Medicine {medicine_name} not found"}

        adjusted_stock = med.stock_quantity + quantity_change
        if adjusted_stock < 0:
            logger.warning("Medicine stock adjustment rejected: insufficient stock")
            return {
                "success": False,
                "message": f"Insufficient stock for {med.name}. Available: {med.stock_quantity}.",
            }

        med.stock_quantity = adjusted_stock
        session.add(
            InventoryTransaction(
                medicine_id=med.id,
                quantity_change=quantity_change,
                reason=normalized_reason,
            )
        )
        await session.commit()
        await session.refresh(med)
        logger.info(
            "Medicine stock adjusted (medicine_id=%s, quantity_change=%s)",
            med.id,
            quantity_change,
        )
        return {
            "success": True,
            "medicine": med.name,
            "new_stock": med.stock_quantity,
            "quantity_change": quantity_change,
            "reason": normalized_reason,
        }