from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from .schema import *
import uuid
from .service import RecordService
from database import get_db
from models.user import ModeEnum, ToolEnum

router = APIRouter(prefix="/api/records", tags=["records"])

allow_fields = [
    "user_id",
    "mode",
    "place",
    "tool",
]

@router.get("/")
def get_records_endpoint(mode: str = None, place: str = None, tool: str = None, db: Session = Depends(get_db)):
    records = RecordService.get_records(db, mode=mode, place=place, tool=tool)
    return records

@router.get("/{id}")
def get_record_endpoint(id: uuid.UUID, db: Session = Depends(get_db)):
    records = RecordService.get_record_by_ID(db, id=id)
    return records

@router.get("/{user_id}")
def get_record_by_userID_endpoint(user_id: uuid.UUID, mode: str = None, place: str = None, tool: str = None, db: Session = Depends(get_db)):
    records = RecordService.get_record(db, user_id=user_id, mode=mode, place=place, tool=tool)
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