from pydantic import BaseModel, Field, validator, ConfigDict
from datetime import datetime, date
from uuid import UUID
from typing import Optional, List, Any
from enum import Enum


class RecordBase(BaseModel):
    id: UUID
    task_id: UUID
    user_id: Optional[UUID] = None

class RecordCreate(BaseModel):
    task_id: UUID
    user_id: Optional[UUID] = None
    mode : str
    place : str
    tool : List[str]

    @validator("occurred_at", pre=True, always=True)
    def set_occurred_at_now_if_missing(cls, v):
        return v or datetime.now()

    @validator("occurred_at")
    def not_in_future(cls, v: datetime):
        if v > datetime.now():
            raise ValueError("occurred_at cannot be in the future")
        return v

# Data for the LLM
class RecordResponse(RecordBase):
    duration_seconds: Optional[int] = None
    mode: Optional[str] = None
    place: Optional[str] = None
    tool: Optional[List[str]] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)
    class Config:
        orm_mode = True