from fastapi import APIRouter
from typing import List
import uuid
from .schema import *
from .service import *

router = APIRouter(prefix="/api/records", tags=["records"])

@router.get("/")
async def get_records() -> List[RecordResponse]:
    return get_records()

@router.post("/")
async def create_record(record: RecordCreate):
    return create_record(record)

@router.put("/{record_id}")
async def update_record(record_id: uuid.UUID, record: RecordUpdate):
    return update_record(record_id, record)