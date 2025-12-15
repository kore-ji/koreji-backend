from datetime import date, datetime
from typing import List, Optional
from pydantic import BaseModel, Field
from models.task import TaskStatus, TaskPriority
from uuid import UUID

try:
    # Pydantic v2
    from pydantic import ConfigDict
    V2 = True
except Exception:
    V2 = False

# ----- Tag & TagGroup -----
class TagGroupBase(BaseModel):
    name: str
    is_single_select: bool = False
    allow_add_tag: bool = True


class TagGroupCreate(TagGroupBase):
    pass


class TagGroupUpdate(BaseModel):
    name: Optional[str] = None
    is_single_select: Optional[bool] = None
    allow_add_tag: Optional[bool] = None


class TagGroupResponse(TagGroupBase):
    id: UUID
    type: str
    created_at: datetime

    if V2:
        model_config = ConfigDict(from_attributes=True)
    else:
        class Config:
            orm_mode = True

class TagBase(BaseModel):
    name: str
    tag_group_id: UUID


class TagCreate(TagBase):
    pass


class TagUpdate(BaseModel):
    name: Optional[str] = None
    tag_group_id: Optional[UUID] = None


class TagResponse(TagBase):
    id: UUID
    is_system: bool
    created_at: datetime

    if V2:
        model_config = ConfigDict(from_attributes=True)
    else:
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
    tag_ids: list[UUID] = Field(default_factory=list)

class SubtaskCreate(BaseModel):
    task_id: UUID
    title: str
    description: Optional[str] = None
    due_date: Optional[datetime] = None
    status: TaskStatus = TaskStatus.pending
    estimated_minutes: Optional[int] = None
    actual_minutes: Optional[int] = None
    tag_ids: list[UUID] = Field(default_factory=list)

class SubtaskUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    due_date: Optional[datetime] = None
    status: Optional[TaskStatus] = None
    estimated_minutes: Optional[int] = None
    actual_minutes: Optional[int] = None
    tag_ids: Optional[list[UUID]] = None

    if V2:
        model_config = ConfigDict(from_attributes=True)
    else:
        class Config:
            orm_mode = True



class TaskUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    due_date: Optional[date] = None
    status: Optional[TaskStatus] = None
    priority: Optional[TaskPriority] = None
    estimated_minutes: Optional[int] = None
    actual_minutes: Optional[int] = None
    category: Optional[str] = None
    tag_ids: Optional[list[UUID]] = None

class TaskResponse(TaskBase):
    id: UUID
    is_subtask: bool
    parent_id: Optional[UUID]
    category: Optional[str]
    # progress is not save in DB, which is calculated from subtasks and then included in the response
    progress: float = 0.0

    tags: List[TagResponse] = Field(default_factory=list)
    subtasks: List["TaskResponse"] = Field(default_factory=list)

    if V2:
        model_config = ConfigDict(from_attributes=True)
    else:
        class Config:
            orm_mode = True

class SubtaskResponse(TaskResponse):
    pass

# ----- update task tags -----
class UpdateTaskTagsRequest(BaseModel):
    tag_ids: List[UUID]

# ----- AI related -----
class GenerateSubtasksRequest(BaseModel):
    pass

class GeneratedSubtask(BaseModel):
    id: str
    title: str
    description: str | None
    estimated_minutes: int | None

class GenerateSubtasksResponse(BaseModel):
    subtasks: List[GeneratedSubtask]

# ----- Regenerate Subtasks Questions -----
class QuestionsRequest(TaskResponse):
    pass

class QuestionsResponse(BaseModel):
    questions: List[str]

class RegenerateSubtasksRequest(BaseModel):
    questions: List[str]
    answers: List[str]

try:
    TaskResponse.model_rebuild() 
except AttributeError:
    TaskResponse.update_forward_refs()