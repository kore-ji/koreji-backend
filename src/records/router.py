from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from .schema import *
import uuid
from .service import RecordService
from database import get_db

router = APIRouter(prefix="/api/records", tags=["records"])

allow_fields = [
    "user_id",
    "mode",
    "place",
    "tool",
]

@router.get("/")
def get_records_endpoint(user_id: uuid.UUID = None, mode: str = None, place: str = None, tool: list = None, db: Session = Depends(get_db)):
    records = RecordService.get_records(db, user_id=user_id, mode=mode, place=place, tool=tool)
    return records

@router.post("/", response_model=RecordResponse)
def create_record_endpoint(record: RecordCreate, db: Session = Depends(get_db)):
    new_record = RecordService.create_record(db, record)
    if not new_record:
        raise HTTPException(status_code=400, detail="Record creation failed")
    return new_record

@router.put("/{id}", response_model=RecordResponse)
def update_record_endpoint(id: uuid.UUID, record: RecordUpdate, db: Session = Depends(get_db)):
    updated_record = RecordService.update_record(db, id, record)
    if not updated_record:
        raise HTTPException(status_code=404, detail="Record not found")
    return updated_record