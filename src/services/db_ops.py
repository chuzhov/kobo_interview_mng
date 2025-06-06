# services/db_ops.py
from typing import List

from sqlalchemy import func, insert, select
from sqlalchemy.exc import IntegrityError

from core.database import AsyncSessionLocal
from models.interviews import Interview
from services.logger import logger


async def get_all_records():
    """Retrieve all records from the Interview table.
    Returns:
        List[Interview]: A list of Interview records.
    """
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(Interview))
        return result.scalars().all()


async def insert_new_records(submissions: List[dict]):
    """Insert new records into the Interview table.
    Args:
        submissions (List[dict]): A list of dictionaries representing the records to be inserted.
    """
    async with AsyncSessionLocal() as session:
        try:

            # Perform a bulk insert
            await session.execute(
                insert(Interview).values(submissions)
                # .using_on_conflict_do_nothing()  # Uncomment if using PostgreSQL with ON CONFLICT DO NOTHING
            )
            await session.commit()
            logger.info(f"Inserted {len(submissions)} new records into the database.")
        except IntegrityError:
            await session.rollback()
            logger.warning("IntegrityError occurred during bulk insert.")
        except Exception as e:
            await session.rollback()
            logger.error(f"Error during bulk insert: {str(e)}")


async def get_existing_uuids() -> set:
    """Retrieve existing UUIDs from the database.
    Returns:
        set: A set of existing UUIDs.
    """
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(Interview.uuid))
        return {row[0] for row in result.fetchall()}


async def get_records_count() -> int|None:
    """Get the count of records in the Interview table.
    Returns:
        int: The count of records.
    """
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(func.count()).select_from(Interview))
        return result.scalar()
