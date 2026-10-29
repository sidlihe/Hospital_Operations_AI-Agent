import asyncio
from src.core.database import init_db, AsyncSessionLocal
from src.models.db_models import Doctor, Bed, BedType, BedStatus, Medicine


async def seed():
    await init_db()
    async with AsyncSessionLocal() as session:
        # 1. Seed Doctors
        doctors = [
            Doctor(name="Dr. Sarah Smith", specialty="Cardiology", shift_start="08:00", shift_end="16:00", is_on_duty=True),
            Doctor(name="Dr. James Patel", specialty="Emergency Medicine", shift_start="00:00", shift_end="23:59", is_on_duty=True),
            Doctor(name="Dr. Emily Chen", specialty="Orthopedics", shift_start="09:00", shift_end="17:00", is_on_duty=True),
        ]
        session.add_all(doctors)

        # 2. Seed Beds
        beds = [
            Bed(room_number="ICU-101", bed_type=BedType.ICU, status=BedStatus.AVAILABLE),
            Bed(room_number="ICU-102", bed_type=BedType.ICU, status=BedStatus.AVAILABLE),
            Bed(room_number="ER-201", bed_type=BedType.EMERGENCY, status=BedStatus.AVAILABLE),
            Bed(room_number="GEN-301", bed_type=BedType.GENERAL, status=BedStatus.AVAILABLE),
            Bed(room_number="GEN-302", bed_type=BedType.GENERAL, status=BedStatus.AVAILABLE),
        ]
        session.add_all(beds)

        # 3. Seed Medicines
        medicines = [
            Medicine(name="Epinephrine", stock_quantity=15, burn_rate_per_day=5.0, minimum_threshold=25, unit_price=20.0),
            Medicine(name="Amoxicillin", stock_quantity=120, burn_rate_per_day=10.0, minimum_threshold=30, unit_price=5.5),
            Medicine(name="Propofol", stock_quantity=8, burn_rate_per_day=4.0, minimum_threshold=20, unit_price=45.0),
        ]
        session.add_all(medicines)

        await session.commit()
        print("Database initialized and mock hospital resources seeded successfully!")


if __name__ == "__main__":
    asyncio.run(seed())