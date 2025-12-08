from datetime import date
from typing import List, Optional
from pydantic import BaseModel
from models.task import TaskStatus, TaskPriority
from uuid import UUID

# ----- Tag & TagGroup -----
class TagGroupBase(BaseModel):
    name: str


class TagGroupCreate(TagGroupBase):
    pass


# class TagGroupUpdate(BaseModel):
#     name: Optional[str] = None


class TagGroupResponse(TagGroupBase):
    id: UUID
    type: str
    is_system: bool

    class Config:
        orm_mode = True


class TagBase(BaseModel):
    name: str
    tag_group_id: UUID


class TagCreate(TagBase):
    pass


# class TagUpdate(BaseModel):
#     name: Optional[str] = None
#     tag_group_id: Optional[str] = None


class TagResponse(TagBase):
    id: UUID
    is_system: bool

    class Config:
        orm_mode = True

# ----- Task -----
class TaskBase(BaseModel):
    title: str
    description: Optional[str] = None
    due_date: Optional[date] = None
    status: TaskStatus = TaskStatus.pending
    priority: Optional[TaskPriority] = None
    estimated_minutes: Optional[int] = None
    actual_minutes: Optional[int] = None


class TaskCreate(TaskBase):
    category: Optional[str] = None

class SubtaskCreate(TaskBase):
    task_id: UUID


class TaskUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    due_date: Optional[date] = None
    status: Optional[TaskStatus] = None
    priority: Optional[TaskPriority] = None
    estimated_minutes: Optional[int] = None
    actual_minutes: Optional[int] = None
    category: Optional[str] = None

class TaskResponse(TaskBase):
    id: UUID
    is_subtask: bool
    parent_id: Optional[UUID]
    category: Optional[str]
    # progress is not save in DB, which is calculated from subtasks and then included in the response
    progress: float = 0.0

    tags: List[TagResponse] = []
    subtasks: List[TaskResponse] = []

    class Config:
        orm_mode = True

# ----- update task tags -----
class UpdateTaskTagsRequest(BaseModel):
    tag_ids: List[UUID]

# ----- AI related -----
class GenerateSubtasksRequest(BaseModel):
    max_subtasks: int = 8


class GenerateSubtasksResponse(BaseModel):
    subtasks: List[TaskResponse]