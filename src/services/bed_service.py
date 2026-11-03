from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from src.models.db_models import Bed, BedType, BedStatus
from src.core.logger import logger

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
            logger.warning("Bed allocation failed: no available bed of type %s", bed_type.value)
            return {"success": False, "message": f"No beds available for type {bed_type.value}"}

        bed.status = BedStatus.OCCUPIED
        bed.assigned_patient_id = patient_id
        await session.commit()
        await session.refresh(bed)
        logger.info("Bed allocated (type=%s)", bed.bed_type.value)

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
            logger.warning("Bed release failed: bed not found")
            return {"success": False, "message": "Bed not found"}

        bed.status = BedStatus.AVAILABLE
        bed.assigned_patient_id = None
        await session.commit()
        logger.info("Bed released")
        return {"success": True, "message": f"Bed {bed.room_number} released and marked available."}

if __name__ == "__main__":
    import asyncio
    from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
    from sqlalchemy.orm import sessionmaker
    from src.config import settings

    DATABASE_URL = settings.DATABASE_URL

    async def main():
        engine = create_async_engine(DATABASE_URL, echo=settings.SQL_ECHO)
        async_session = sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)

        try:
            async with async_session() as session:
                bed_service = BedService()

                # Example usage of get_bed_counts
                counts = await bed_service.get_bed_counts(session)
                logger.info("Bed counts: %s", counts)

                # Example usage of allocate_bed
                allocation_result = await bed_service.allocate_bed(session, patient_id=1, bed_type=BedType.GENERAL)
                logger.info("Bed allocation completed (success=%s)", allocation_result["success"])

                # Example usage of release_bed
                if allocation_result["success"]:
                    release_result = await bed_service.release_bed(session, bed_id=allocation_result["bed_id"])
                    logger.info("Bed release completed (success=%s)", release_result["success"])
        finally:
            await engine.dispose()

    asyncio.run(main())