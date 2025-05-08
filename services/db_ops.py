# services/db_ops.py
from sqlalchemy import select, insert
from sqlalchemy.exc import IntegrityError
from core.database import AsyncSessionLocal
from typing import List
from services.logger import logger

from models.interviews import Interview
import schemas.kobo_schema as schemas

async def get_all_records():
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(Interview))
        return result.scalars().all()

async def insert_new_records(submissions: List[Interview]):
    async with AsyncSessionLocal() as session:
        try:
            
            # Perform a bulk insert
            await session.execute(
                insert(Interview)
                .values(submissions)
                .on_conflict_do_nothing()  # Skip duplicates
            )
            await session.commit()
        except IntegrityError:
            await session.rollback()
            logger.warning("IntegrityError occurred during bulk insert.")
        except Exception as e:
            await session.rollback()
            logger.error(f"Error during bulk insert: {str(e)}")

async def get_records_count():
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(Interview).count())
        return result.scalar()