from pydantic import BaseModel, Field, validator, ConfigDict
from datetime import datetime, date
from uuid import UUID
from typing import Optional, List, Any
from enum import Enum

class EventType(str, Enum):
    INPROGRESS = "INPROGRESS"
    PAUSE_START = "PAUSE_START"
    PAUSE_END = "PAUSE_END"
    QUIT = "QUIT"
    COMPLETE = "COMPLETE"

class RecordBase(BaseModel):
    task_id: UUID
    user_id: Optional[UUID] = None

class RecordCreate(BaseModel):
    task_id: UUID
    user_id: Optional[UUID] = None
    mode : str
    place : str
    tool : List[str]
    occurred_at: datetime

# Data for the LLM
class RecordResponse(RecordBase):
    id: UUID
    duration_seconds: Optional[int] = None
    mode: Optional[str] = None
    place: Optional[str] = None
    tool: Optional[List[str]] = None
    event_type : EventType
    occurred_at: datetime

    model_config = ConfigDict(from_attributes=True)

class RecordUpdate(RecordBase):
    event_type : EventType
    updated_at: datetime
