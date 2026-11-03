import asyncio
from sqlalchemy import func, or_, select
from src.core.database import init_db, AsyncSessionLocal
from src.models.db_models import Doctor, Bed, BedType, BedStatus, Medicine, Patient, PriorityLevel


async def seed():
    # Creates the configured database and all mapped tables when the file is absent.
    await init_db()
    async with AsyncSessionLocal() as session:
        added = {"doctors": 0, "beds": 0, "medicines": 0, "patients": 0}

        doctors = [
            Doctor(name="Dr. Sarah Smith", specialty="Cardiology", shift_start="08:00", shift_end="16:00", is_on_duty=True),
            Doctor(name="Dr. James Patel", specialty="Emergency Medicine", shift_start="00:00", shift_end="23:59", is_on_duty=True),
            Doctor(name="Dr. Emily Chen", specialty="Orthopedics", shift_start="09:00", shift_end="17:00", is_on_duty=True),
        ]
        for doctor in doctors:
            existing_doctor = await session.execute(
                select(Doctor.id).where(
                    func.lower(Doctor.name) == doctor.name.lower(),
                    func.lower(Doctor.specialty) == doctor.specialty.lower(),
                )
            )
            if existing_doctor.scalar_one_or_none() is None:
                session.add(doctor)
                added["doctors"] += 1

        beds = [
            Bed(room_number="ICU-101", bed_type=BedType.ICU, status=BedStatus.AVAILABLE),
            Bed(room_number="ICU-102", bed_type=BedType.ICU, status=BedStatus.AVAILABLE),
            Bed(room_number="ER-201", bed_type=BedType.EMERGENCY, status=BedStatus.AVAILABLE),
            Bed(room_number="GEN-301", bed_type=BedType.GENERAL, status=BedStatus.AVAILABLE),
            Bed(room_number="GEN-302", bed_type=BedType.GENERAL, status=BedStatus.AVAILABLE),
        ]
        for bed in beds:
            existing_bed = await session.execute(
                select(Bed.id).where(Bed.room_number == bed.room_number)
            )
            if existing_bed.scalar_one_or_none() is None:
                session.add(bed)
                added["beds"] += 1

        medicines = [
            Medicine(name="Epinephrine", stock_quantity=15, burn_rate_per_day=5.0, minimum_threshold=25, unit_price=20.0),
            Medicine(name="Amoxicillin", stock_quantity=120, burn_rate_per_day=10.0, minimum_threshold=30, unit_price=5.5),
            Medicine(name="Propofol", stock_quantity=8, burn_rate_per_day=4.0, minimum_threshold=20, unit_price=45.0),
        ]
        for medicine in medicines:
            existing_medicine = await session.execute(
                select(Medicine.id).where(func.lower(Medicine.name) == medicine.name.lower())
            )
            if existing_medicine.scalar_one_or_none() is None:
                session.add(medicine)
                added["medicines"] += 1

        # Keep the sample patient idempotent across repeated seed runs.
        sample_patient = Patient(
            mrn="MRN-2026-INIT01",
            name="John Doe",
            age=45,
            phone="+1-555-0199",
            email="johndoe@example.com",
            priority=PriorityLevel.LEVEL_5_NON_URGENT
        )
        existing_patient = await session.execute(
            select(Patient.id).where(
                or_(
                    Patient.mrn == sample_patient.mrn,
                    Patient.phone == sample_patient.phone,
                    func.lower(Patient.email) == sample_patient.email.lower(),
                )
            )
        )
        if existing_patient.scalar_one_or_none() is None:
            session.add(sample_patient)
            added["patients"] += 1

        await session.commit()
        print(
            "Seed complete. Added "
            f"{added['doctors']} doctors, {added['beds']} beds, "
            f"{added['medicines']} medicines, and {added['patients']} patients."
        )


if __name__ == "__main__":
    asyncio.run(seed())