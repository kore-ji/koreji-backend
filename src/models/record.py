import uuid
from enum import Enum as PyEnum
from sqlalchemy import ARRAY, Column, DateTime, Enum, Integer, Text, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from datetime import datetime
from database import Base


class EventType(PyEnum):
    INPROGRESS = "INPROGRESS"
    PAUSE_START = "PAUSE_START"
    PAUSE_END = "PAUSE_END"
    QUIT = "QUIT"
    COMPLETE = "COMPLETE"

class Record(Base):
    __tablename__ = 'records'
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, unique=True, nullable=False)
    task_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id'), nullable=False, index=True)

    mode = Column(Text, nullable=True)
    place = Column(Text, nullable=True)
    tool = Column(ARRAY(Text), nullable=True)

    event_type = Column(Enum(EventType, name="event_type"), nullable=False)
    duration_seconds = Column(Integer, nullable=True)
    occurred_at = Column(DateTime(timezone=True), default=datetime.now, nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), default=datetime.now, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=datetime.now, onupdate=datetime.now, nullable=False)