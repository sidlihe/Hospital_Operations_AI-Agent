import asyncio
from src.core.database import AsyncSessionLocal
from src.services.doctor_service import DoctorService
from src.services.inventory_service import InventoryService
from src.services.emergency_service import EmergencyService

async def test():
    async with AsyncSessionLocal() as session:
        docs = await DoctorService.get_available_doctors(session)
        print(f"Available Doctors: {len(docs)}")

        shortages = await InventoryService.predict_shortages(session)
        print("Inventory Shortage Warnings:")
        for s in shortages:
            if s.is_shortage_critical:
                print(f" - {s.medicine_name}: {s.days_until_stockout} days left")

        triage = EmergencyService.classify_esi("Patient has severe chest pain and radiating arm numbness")
        print(f"Triage Result: {triage['priority'].value} -> {triage['recommended_bed'].value}")

if __name__ == "__main__":
    asyncio.run(test())