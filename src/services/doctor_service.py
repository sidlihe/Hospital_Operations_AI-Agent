from datetime import datetime
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession
from src.models.db_models import Doctor, Appointment, AppointmentStatus

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
        return {
            "success": True,
            "appointment_id": appointment.id,
            "start_time": appointment.start_time.isoformat()
        }