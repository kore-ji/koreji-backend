from http.client import HTTPException
from fastapi import APIRouter
from typing import List
import uuid
from .schema import *
from .service import *

router = APIRouter(prefix="/api/records", tags=["records"])

@router.get("/")
async def get_records() -> List[RecordResponse]:
    records = get_records()
    if records is None:
        return HTTPException(status_code=404, detail="Records not found")
    return records

@router.post("/")
async def create_record(record: RecordCreate):
    record = create_record(record)
    if not record:
        return HTTPException(status_code=400, detail="Record creation failed")
    return record

@router.put("/{record_id}")
async def update_record(record_id: uuid.UUID, record: RecordUpdate):
    record = update_record(record_id, record)
    if not record:
        return HTTPException(status_code=404, detail="Record not found")
    return record