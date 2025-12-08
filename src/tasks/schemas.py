from datetime import date
from typing import List, Optional
from pydantic import BaseModel
from models.task import SubtaskStatus, SubtaskPriority
from uuid import UUID

# ----- Tag & TagGroup -----
class TagGroupBase(BaseModel):
    name: str


class TagGroupCreate(TagGroupBase):
    pass


class TagGroupUpdate(BaseModel):
    name: Optional[str] = None


class TagGroupResponse(TagGroupBase):
    id: UUID

    class Config:
        orm_mode = True


class TagBase(BaseModel):
    name: str
    tag_group_id: UUID


class TagCreate(TagBase):
    pass


class TagUpdate(BaseModel):
    name: Optional[str] = None
    tag_group_id: Optional[str] = None


class TagResponse(TagBase):
    id: UUID

    class Config:
        orm_mode = True

# ----- Subtask -----
class SubtaskBase(BaseModel):
    title: str
    description: Optional[str] = None
    priority: SubtaskPriority = SubtaskPriority.medium
    status: SubtaskStatus = SubtaskStatus.pending
    estimated_minutes: Optional[int] = None


class SubtaskCreate(SubtaskBase):
    task_id: UUID


class SubtaskUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    priority: Optional[SubtaskPriority] = None
    status: Optional[SubtaskStatus] = None
    estimated_minutes: Optional[int] = None


class SubtaskResponse(SubtaskBase):
    id: UUID
    actual_minutes: Optional[int] = None
    tags: List[TagResponse] = []

    class Config:
        orm_mode = True

# ----- Task -----
class TaskBase(BaseModel):
    title: str
    description: Optional[str] = None
    category: Optional[str] = None   # "School", "Work"...
    due_date: Optional[date] = None


class TaskCreate(TaskBase):
    pass


class TaskUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    category: Optional[str] = None
    due_date: Optional[date] = None


class TaskResponse(TaskBase):
    id: UUID
    # progress is not save in DB, which is calculated from subtasks and then included in the response
    progress: float = 0.0
    subtasks: List[SubtaskResponse] = []

    class Config:
        orm_mode = True

# ----- AI related -----
class GenerateSubtasksRequest(BaseModel):
    max_subtasks: int = 8


class GenerateSubtasksResponse(BaseModel):
    subtasks: List[SubtaskResponse]