import uuid
from datetime import datetime
from sqlalchemy import Column, String, Text, Integer, Date, DateTime, Enum, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database import Base
import enum

# ----- Enums -----
class SubtaskStatus(str, enum.Enum):
    pending = "pending"
    in_progress = "in_progress"
    completed = "completed"
    archeieved = "archieved"

class SubtaskPriority(str, enum.Enum):
    low = "low"
    medium = "medium"
    high = "high"

# ----- Task Model -----
class Task(Base):
    __tablename__ = "tasks"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)

    title = Column(String, nullable=False)
    description = Column(Text, nullable=True)

    category = Column(String, nullable=True) 
    due_date = Column(Date, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    subtasks = relationship("Subtask", back_populates="task", cascade="all, delete-orphan")

# ----- Subtask Model -----
class Subtask(Base):
    __tablename__ = "subtasks"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, nullable=False)
    task_id = Column(UUID(as_uuid=True), ForeignKey("tasks.id"), nullable=False)

    title = Column(String, nullable=False)
    description = Column(Text, nullable=True)

    status = Column(Enum(SubtaskStatus), default=SubtaskStatus.pending, nullable=False)
    priority = Column(Enum(SubtaskPriority), default=SubtaskPriority.medium, nullable=False)

    estimated_minutes = Column(Integer, nullable=True)
    actual_minutes = Column(Integer, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    task = relationship("Task", back_populates="subtasks")

    tags = relationship(
        "Tag",
        secondary="subtask_tags",
        back_populates="subtasks",
    )

# ----- Tag Group Model -----
class TagGroup(Base):
    __tablename__ = "tag_groups"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, nullable=False)
    name = Column(String, nullable=False)

    tags = relationship("Tag", back_populates="group", cascade="all, delete-orphan")

# ----- Tag Model -----
class Tag(Base):
    __tablename__ = "tags"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, nullable=False)
    tag_group_id = Column(UUID(as_uuid=True), ForeignKey("tag_groups.id"), nullable=False)

    name = Column(String, nullable=False)

    group = relationship("TagGroup", back_populates="tags")

    subtasks = relationship(
        "Subtask",
        secondary="subtask_tags",
        back_populates="tags"
    )

# ----- Join Table：Subtask-Tag -----
class SubtaskTag(Base):
    __tablename__ = "subtask_tags"

    subtask_id = Column(UUID(as_uuid=True), ForeignKey("subtasks.id", ondelete="CASCADE"), primary_key=True)
    tag_id = Column(UUID(as_uuid=True), ForeignKey("tags.id", ondelete="CASCADE"), primary_key=True)