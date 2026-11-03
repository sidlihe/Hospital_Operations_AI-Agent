import uuid
from datetime import datetime
from sqlalchemy import select, or_
from sqlalchemy.ext.asyncio import AsyncSession
from src.models.db_models import Patient, Consultation, PriorityLevel, EncounterType
from src.core.logger import logger


class PatientService:
    @staticmethod
    async def get_or_create_patient(
        session: AsyncSession,
        name: str,
        phone: str,
        email: str,
        age: int = 30,
        gender: str = "Not Specified"
    ) -> tuple[Patient, bool]:
        """
        Deduplicates patients by phone OR email.
        If exists -> returns existing record.
        If new -> generates unique MRN and saves to DB.
        """
        query = select(Patient).where(
            or_(
                Patient.phone == phone.strip(),
                Patient.email == email.strip().lower()
            )
        )
        existing = (await session.execute(query)).scalar_one_or_none()
        
        if existing:
            logger.info(f"[PatientService] Existing patient identified: MRN={existing.mrn} | Name={existing.name}")
            return existing, False

        # Generate unique hospital MRN (e.g. MRN-2026-A1B2)
        new_mrn = f"MRN-{datetime.utcnow().year}-{uuid.uuid4().hex[:6].upper()}"
        patient = Patient(
            mrn=new_mrn,
            name=name.strip(),
            phone=phone.strip(),
            email=email.strip().lower(),
            age=age,
            gender=gender,
            priority=PriorityLevel.LEVEL_5_NON_URGENT
        )
        session.add(patient)
        await session.commit()
        await session.refresh(patient)

        logger.info(f"[PatientService] Created new patient: MRN={patient.mrn} | Name={patient.name}")
        return patient, True

    @staticmethod
    async def record_consultation(
        session: AsyncSession,
        patient_id: int,
        doctor_id: int | None,
        encounter_type: EncounterType,
        symptoms: str,
        vitals: str,
        triage_priority: PriorityLevel,
        decision_log: str,
        patient_summary: str,
        orders: str
    ) -> Consultation:
        consultation = Consultation(
            patient_id=patient_id,
            doctor_id=doctor_id,
            encounter_type=encounter_type,
            symptoms=symptoms,
            vitals=vitals,
            triage_priority=triage_priority,
            decision_engine_log=decision_log,
            patient_friendly_summary=patient_summary,
            clinical_orders=orders
        )
        session.add(consultation)
        await session.commit()
        await session.refresh(consultation)
        logger.info(f"[PatientService] Recorded consultation ID={consultation.id} for patient_id={patient_id}")
        return consultation

    @staticmethod
    async def get_patient_history(session: AsyncSession, patient_id_or_mrn: str) -> dict | None:
        """
        Retrieves complete medical record history:
        - Demographic details
        - All historical consultations & Decision Engine logs
        - All appointments
        - All billing statements
        """
        from sqlalchemy.orm import selectinload

        # Search by MRN or by integer ID
        if patient_id_or_mrn.isdigit():
            query = select(Patient).where(Patient.id == int(patient_id_or_mrn))
        else:
            query = select(Patient).where(Patient.mrn == patient_id_or_mrn.strip())

        query = query.options(
            selectinload(Patient.consultations),
            selectinload(Patient.appointments),
            selectinload(Patient.bills)
        )

        result = await session.execute(query)
        patient = result.scalar_one_or_none()

        if not patient:
            return None

        return {
            "patient": {
                "id": patient.id,
                "mrn": patient.mrn,
                "name": patient.name,
                "phone": patient.phone,
                "email": patient.email,
                "registered_on": patient.created_at.isoformat()
            },
            "total_visits": len(patient.consultations),
            "consultations": [
                {
                    "consultation_id": c.id,
                    "date": c.created_at.isoformat(),
                    "type": c.encounter_type.value,
                    "triage_priority": c.triage_priority.value,
                    "symptoms": c.symptoms,
                    "summary": c.patient_friendly_summary,
                    "clinical_orders": c.clinical_orders,
                    "decision_log": c.decision_engine_log
                }
                for c in sorted(patient.consultations, key=lambda x: x.created_at, reverse=True)
            ],
            "appointments": [
                {
                    "appointment_id": a.id,
                    "doctor_id": a.doctor_id,
                    "time": a.start_time.isoformat(),
                    "status": a.status.value
                }
                for a in sorted(patient.appointments, key=lambda x: x.start_time, reverse=True)
            ],
            "bills": [
                {
                    "bill_id": b.id,
                    "amount_due": b.total_amount,
                    "is_paid": b.is_paid,
                    "details": b.details,
                    "date": b.created_at.isoformat()
                }
                for b in sorted(patient.bills, key=lambda x: x.created_at, reverse=True)
            ]
        }