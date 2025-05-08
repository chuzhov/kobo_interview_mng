# api/endpoints.py
from fastapi import APIRouter
from services.db_ops import get_all_records

router = APIRouter()

@router.get("/interviews")
async def read_records():
    return await get_all_records()