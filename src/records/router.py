from typing import List
import uuid
import schema
from fastAPI import APIRouter

router = APIRouter(prefix="/api/records", tags=["records"])

@router.get("/")
async def get_records() -> List[schema.RecordResponse]:
    pass

@router.post("/")
async def create_record(record: schema.RecordCreate):
    pass

@router.put("/{record_id}")
async def update_record(record_id: uuid.UUID, record: schema.RecordUpdate):
    pass