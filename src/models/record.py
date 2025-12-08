import uuid
from enum import Enum as PyEnum
from sqlalchemy import ARRAY, Column, DateTime, Enum, Integer, Text
from sqlalchemy.dialects.postgresql import UUID, JSONB
from datetime import datetime
from database import Base
import user


class Record(Base):
    __tablename__ = 'records'
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, unique=True, nullable=False)
    task_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    user_id = Column(UUID(as_uuid=True), nullable=False, index=True, references='users.id')
    
    mode = Column(Enum(user.ModeEnum), nullable=False)
    place = Column(Text, nullable=False)
    tool = Column(ARRAY(Enum(user.ToolEnum)), nullable=False)

    duration_seconds = Column(Integer, nullable=True)
    created_at = Column(DateTime, default=datetime.now, nullable=False)
    updated_at = Column(DateTime, default=datetime.now, nullable=False)