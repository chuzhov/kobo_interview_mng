# api/endpoints.py
from fastapi import APIRouter

from services.db_ops import get_all_records, get_records_count

router = APIRouter()


@router.get("/interviews")
async def read_records():
    """Fetch all interview records."""
    return await get_all_records()


@router.get("/interviews/count", status_code=200)
async def status():
    """Return the status of the server."""
    int_count = await get_records_count()
    return {"interviews_count": int_count}
