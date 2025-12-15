from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from database import get_db
from tasks.schemas import (
    TaskCreate,
    TaskResponse,
    TaskUpdate,
    SubtaskCreate,
    SubtaskUpdate,
    TagGroupCreate,
    TagGroupResponse,
    TagCreate,
    TagResponse,
    GenerateSubtasksRequest,
    GenerateSubtasksResponse,
    UpdateTaskTagsRequest,
)

from models.task import TaskStatus, TaskPriority
from tasks import service

from typing import Annotated, Literal

router = APIRouter(prefix="/api/tasks", tags=["tasks"])

# ----- Task CRUD -----

@router.post("/", response_model=TaskResponse)
def create_task(payload: TaskCreate, db: Session = Depends(get_db)):
    return service.create_task(db, payload)


# @router.get("/{task_id}", response_model=TaskResponse)
# def get_task(task_id: UUID, db: Session = Depends(get_db)):
#     task = service.get_task(db, task_id)
#     if not task:
#         raise HTTPException(404, "Task not found")
#     return task


# @router.patch("/{task_id}", response_model=TaskResponse)
# def update_task(task_id: UUID, payload: TaskUpdate, db: Session = Depends(get_db)):
#     task = service.update_task(db, task_id, payload)
#     if not task:
#         raise HTTPException(404, "Task not found")
#     return task

# ----- Task List -----
@router.get("/", response_model=list[TaskResponse])
def list_tasks(
    is_subtask: bool | None = None,
    parent_id: UUID | None = None,
    status: TaskStatus | None = None,
    category: str | None = None,
    tag_ids: Annotated[list[UUID] | None, Query()] = None,
    match: Literal["any", "all"] = "any",
    db: Session = Depends(get_db),
):
    """
    Use case:
    - Only view top-level tasks: /tasks?is_subtask=false
    - View tasks by category: /tasks?category=School
    - View subtasks and tasks without subtasks: /tasks?is_subtask=true
      (includes both subtasks and top-level tasks that have no children)
    - View subtasks under a specific task: /tasks?is_subtask=true&parent_id=<task_id>
      (There is also a dedicated endpoint /tasks/{task_id}/subtasks)
    """
    return service.list_tasks(
        db,
        is_subtask=is_subtask,
        parent_id=parent_id,
        status=status,
        category=category,
        tag_ids=tag_ids,
        match=match,
    )

@router.get("/{task_id}/subtasks", response_model=list[TaskResponse])
def list_subtasks(task_id: UUID, db: Session = Depends(get_db)):
    subtasks = service.list_subtasks_for_task(db, task_id)
    if subtasks is None:
        raise HTTPException(404, "Task not found")
    return subtasks

@router.get("/categories", response_model=list[str])
def list_task_categories(db: Session = Depends(get_db)):
    return service.list_task_categories(db)

# ----- Subtasks (Create/Update) -----
@router.post("/subtasks", response_model=TaskResponse)
def create_subtask(payload: SubtaskCreate, db: Session = Depends(get_db)):
    subtask = service.create_subtask(db, payload)
    if not subtask:
        raise HTTPException(404, "Parent task not found")
    return subtask


@router.patch("/subtasks/{subtask_id}", response_model=TaskResponse)
def update_subtask(subtask_id: UUID, payload: SubtaskUpdate, db: Session = Depends(get_db)):
    subtask = service.update_subtask(db, subtask_id, payload)
    if not subtask:
        raise HTTPException(404, "Subtask not found")
    return subtask

# ----- Task <-> Tags -----
@router.put("/{task_id}/tags", response_model=TaskResponse)
def update_task_tags(task_id: UUID, payload: UpdateTaskTagsRequest, db: Session = Depends(get_db)):
    task = service.update_task_tags(db, task_id, payload)
    if not task:
        raise HTTPException(404, "Task not found")
    return task

# ----- Tag Groups -----
@router.post("/tag-groups", response_model=TagGroupResponse)
def create_tag_group(payload: TagGroupCreate, db: Session = Depends(get_db)):
    return service.create_tag_group(db, payload)


@router.get("/tag-groups", response_model=list[TagGroupResponse])
def list_tag_groups(db: Session = Depends(get_db)):
    return service.list_tag_groups(db)

# ----- Tags -----
@router.post("/tags", response_model=TagResponse)
def create_tag(payload: TagCreate, db: Session = Depends(get_db)):
    return service.create_tag(db, payload)


@router.get("/tag-groups/{group_id}/tags", response_model=list[TagResponse])
def list_tags(group_id: UUID, db: Session = Depends(get_db)):
    return service.list_tags_by_group(db, group_id)

# ----- AI Generate Subtasks -----
@router.post("/{task_id}/generate-subtasks", response_model=GenerateSubtasksResponse)
async def generate_subtasks(task_id: UUID, payload: GenerateSubtasksRequest, db: Session = Depends(get_db)):
    result = await service.generate_subtasks(db, task_id, payload)
    if result is None:
        raise HTTPException(404, "Task not found")
    return result

# ----- Single Task CRUD -----

@router.get("/{task_id}", response_model=TaskResponse)
def get_task(task_id: UUID, db: Session = Depends(get_db)):
    task = service.get_task(db, task_id)
    if not task:
        raise HTTPException(404, "Task not found")
    return task


@router.patch("/{task_id}", response_model=TaskResponse)
def update_task(task_id: UUID, payload: TaskUpdate, db: Session = Depends(get_db)):
    task = service.update_task(db, task_id, payload)
    if not task:
        raise HTTPException(404, "Task not found")
    return task
