from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from src.models.db_models import Bed, BedType, BedStatus

class BedService:
    @staticmethod
    async def get_bed_counts(session: AsyncSession) -> dict[str, int]:
        query = select(Bed.bed_type, Bed.status, func.count(Bed.id)).group_by(Bed.bed_type, Bed.status)
        result = await session.execute(query)
        
        counts = {}
        for b_type, status, count in result.all():
            counts[f"{b_type.value}_{status.value}"] = count
        return counts

    @staticmethod
    async def allocate_bed(session: AsyncSession, patient_id: int, bed_type: BedType) -> dict:
        # Find first available bed of matching type
        query = select(Bed).where(
            Bed.bed_type == bed_type,
            Bed.status == BedStatus.AVAILABLE
        ).limit(1)
        
        bed = (await session.execute(query)).scalar_one_or_none()
        
        # Fallback to GENERAL if EMERGENCY or ICU is not strictly requested
        if not bed and bed_type != BedType.ICU:
            fallback_query = select(Bed).where(
                Bed.bed_type == BedType.GENERAL,
                Bed.status == BedStatus.AVAILABLE
            ).limit(1)
            bed = (await session.execute(fallback_query)).scalar_one_or_none()

        if not bed:
            return {"success": False, "message": f"No beds available for type {bed_type.value}"}

        bed.status = BedStatus.OCCUPIED
        bed.assigned_patient_id = patient_id
        await session.commit()
        await session.refresh(bed)

        return {
            "success": True,
            "bed_id": bed.id,
            "room_number": bed.room_number,
            "type": bed.bed_type.value
        }

    @staticmethod
    async def release_bed(session: AsyncSession, bed_id: int) -> dict:
        bed = await session.get(Bed, bed_id)
        if not bed:
            return {"success": False, "message": "Bed not found"}

        bed.status = BedStatus.AVAILABLE
        bed.assigned_patient_id = None
        await session.commit()
        return {"success": True, "message": f"Bed {bed.room_number} released and marked available."}