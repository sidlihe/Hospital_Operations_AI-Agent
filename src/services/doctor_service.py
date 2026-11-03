from datetime import datetime, timezone
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession
from src.models.db_models import Appointment, AppointmentStatus, Doctor, Patient
from src.core.logger import logger


class DoctorService:
    @staticmethod
    async def get_available_doctors(session: AsyncSession, specialty: str | None = None) -> list[dict]:
        doctors = await DoctorService.get_doctor_roster(session, specialty)
        return [doctor for doctor in doctors if doctor["is_on_duty"]]

    @staticmethod
    async def get_doctor_roster(session: AsyncSession, specialty: str | None = None) -> list[dict]:
        query = select(Doctor)
        if specialty:
            query = query.where(Doctor.specialty.ilike(f"%{specialty}%"))
        
        result = await session.execute(query)
        doctors = result.scalars().all() 
        return [
            {
                "id": doc.id,
                "name": doc.name,
                "specialty": doc.specialty,
                "shift": f"{doc.shift_start} - {doc.shift_end}",
                "is_on_duty": doc.is_on_duty,
            }
            for doc in doctors
        ]

    @staticmethod
    async def set_doctor_availability(
        session: AsyncSession,
        doctor_id: int,
        is_on_duty: bool,
    ) -> dict | None:
        doctor = await session.get(Doctor, doctor_id)
        if not doctor:
            return None

        doctor.is_on_duty = is_on_duty
        await session.commit()
        await session.refresh(doctor)
        logger.info("Doctor availability updated (doctor_id=%s, is_on_duty=%s)", doctor_id, is_on_duty)
        return {
            "id": doctor.id,
            "name": doctor.name,
            "specialty": doctor.specialty,
            "is_on_duty": doctor.is_on_duty,
        }

    @staticmethod
    async def schedule_appointment(
        session: AsyncSession,
        doctor_id: int,
        patient_id: int,
        start_time: datetime
    ) -> dict:
        if start_time.tzinfo is not None:
            start_time = start_time.astimezone(timezone.utc).replace(tzinfo=None)
        if start_time <= datetime.utcnow():
            return {"success": False, "message": "Appointment time must be in the future."}

        doctor = await session.get(Doctor, doctor_id)
        if not doctor:
            return {"success": False, "message": "Doctor not found."}
        if not doctor.is_on_duty:
            return {"success": False, "message": "Doctor is off duty and cannot be scheduled."}
        if not await session.get(Patient, patient_id):
            return {"success": False, "message": "Patient not found."}

        # Check collision
        query = select(Appointment).where(
            and_(
                Appointment.doctor_id == doctor_id,
                Appointment.start_time == start_time,
                Appointment.status == AppointmentStatus.SCHEDULED
            )
        )
        existing = (await session.execute(query)).scalar_one_or_none()
        if existing:
            logger.warning("Appointment booking rejected because the requested slot is occupied")
            return {"success": False, "message": "Doctor already booked at this time slot."}

        appointment = Appointment(
            doctor_id=doctor_id,
            patient_id=patient_id,
            start_time=start_time,
            status=AppointmentStatus.SCHEDULED
        )
        session.add(appointment)
        await session.commit()
        await session.refresh(appointment)
        logger.info("Appointment scheduled")
        return {
            "success": True,
            "appointment_id": appointment.id,
            "start_time": appointment.start_time.isoformat()
        }

if __name__ == "__main__":
    import asyncio
    from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
    from sqlalchemy.orm import sessionmaker
    from src.config import settings
    from datetime import timedelta

    DATABASE_URL = settings.DATABASE_URL

    engine = create_async_engine(DATABASE_URL, echo=settings.SQL_ECHO)
    async_session = sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)

    async def test_doctor_service():
        async with async_session() as session:
            # Test getting available doctors
            doctors = await DoctorService.get_available_doctors(session, specialty="Cardiology")
            logger.info("Available doctors found: %d", len(doctors))

            # Test scheduling an appointment
            if doctors:
                doctor_id = doctors[0]["id"]
                patient_id = 1  # Example patient ID
                start_time = datetime.now() + timedelta(days=1)  # Example future time
                booking_result = await DoctorService.schedule_appointment(session, doctor_id, patient_id, start_time)
                logger.info("Appointment booking completed (success=%s)", booking_result["success"])

    async def run():
        try:
            await test_doctor_service()
        finally:
            await engine.dispose()

    asyncio.run(run())