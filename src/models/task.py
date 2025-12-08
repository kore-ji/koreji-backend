import uuid
from datetime import datetime
from sqlalchemy import Column, String, Text, Integer, Date, DateTime, Enum, ForeignKey, Boolean
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database import Base
import enum

# ----- Enums -----
class TaskStatus(str, enum.Enum):
    pending = "pending"
    in_progress = "in_progress"
    completed = "completed"
    archived = "archived"

class TaskPriority(str, enum.Enum):
    low = "low"
    medium = "medium"
    high = "high"

# ----- Task Model -----
class Task(Base):
    __tablename__ = "tasks"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)

    is_subtask = Column(Boolean, nullable=False, default=False)
    parent_id = Column(UUID(as_uuid=True), ForeignKey("tasks.id"), nullable=True)
    
    title = Column(String, nullable=False)
    description = Column(Text, nullable=True)

    category = Column(String, nullable=True) 
    due_date = Column(Date, nullable=True)

    status = Column(Enum(TaskStatus), default=TaskStatus.pending, nullable=False)
    priority = Column(Enum(TaskPriority), nullable=True)

    estimated_minutes = Column(Integer, nullable=True)
    actual_minutes = Column(Integer, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # relations
    parent = relationship("Task", remote_side=[id], back_populates="subtasks")
    subtasks = relationship("Task", back_populates="parent", cascade="all, delete-orphan")

    tags = relationship(
        "Tag",
        secondary="task_tags",
        back_populates="tasks",
    )

# ----- Tag Group Model -----
class TagGroup(Base):
    __tablename__ = "tag_groups"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, nullable=False)
    name = Column(String, nullable=False)

    type = Column(String, nullable=False, default="custom") # system / custom

    is_system = Column(Boolean, nullable=False, default=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)

    tags = relationship("Tag", back_populates="group", cascade="all, delete-orphan")

# ----- Tag Model -----
class Tag(Base):
    __tablename__ = "tags"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, nullable=False)
    tag_group_id = Column(UUID(as_uuid=True), ForeignKey("tag_groups.id"), nullable=False)

    name = Column(String, nullable=False)

    is_system = Column(Boolean, nullable=False, default=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    
    group = relationship("TagGroup", back_populates="tags")

    tasks = relationship(
        "Task",
        secondary="task_tags",
        back_populates="tags"
    )

# ----- Join Table：Task-Tag -----
class TaskTag(Base):
    __tablename__ = "task_tags"

    task_id = Column(UUID(as_uuid=True), ForeignKey("tasks.id", ondelete="CASCADE"), primary_key=True)
    tag_id = Column(UUID(as_uuid=True), ForeignKey("tags.id", ondelete="CASCADE"), primary_key=True)