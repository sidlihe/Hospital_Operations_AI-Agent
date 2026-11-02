from datetime import datetime
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession
from src.models.db_models import Doctor, Appointment, AppointmentStatus
from src.core.logger import get_logger

logger = get_logger(__name__)

class DoctorService:
    @staticmethod
    async def get_available_doctors(session: AsyncSession, specialty: str | None = None) -> list[dict]:
        query = select(Doctor).where(Doctor.is_on_duty == True)
        if specialty:
            query = query.where(Doctor.specialty.ilike(f"%{specialty}%"))
        
        result = await session.execute(query)
        doctors = result.scalars().all() 
        return [
            {
                "id": doc.id,
                "name": doc.name,
                "specialty": doc.specialty,
                "shift": f"{doc.shift_start} - {doc.shift_end}"
            }
            for doc in doctors
        ]

    @staticmethod
    async def schedule_appointment(
        session: AsyncSession,
        doctor_id: int,
        patient_id: int,
        start_time: datetime
    ) -> dict:
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