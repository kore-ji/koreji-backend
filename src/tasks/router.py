from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from database import get_db
from tasks.schemas import (
    TaskCreate, TaskResponse, TaskUpdate,
    SubtaskCreate, SubtaskUpdate, SubtaskResponse,
    TagGroupCreate, TagGroupResponse,
    TagCreate, TagResponse,
    GenerateSubtasksRequest, GenerateSubtasksResponse
)

from tasks import service


router = APIRouter(prefix="/tasks", tags=["tasks"])

# ----- Task CRUD -----
@router.post("/", response_model=TaskResponse)
def create_task(payload: TaskCreate, db: Session = Depends(get_db)):
    return service.create_task(db, payload)


@router.get("/{task_id}", response_model=TaskResponse)
def get_task(task_id: str, db: Session = Depends(get_db)):
    task = service.get_task(db, task_id)
    if not task:
        raise HTTPException(404, "Task not found")
    return task


@router.patch("/{task_id}", response_model=TaskResponse)
def update_task(task_id: str, payload: TaskUpdate, db: Session = Depends(get_db)):
    return service.update_task(db, task_id, payload)

# ----- subtasks -----
@router.post("/subtasks", response_model=SubtaskResponse)
def create_subtask(payload: SubtaskCreate, db: Session = Depends(get_db)):
    return service.create_subtask(db, payload)


@router.patch("/subtasks/{subtask_id}", response_model=SubtaskResponse)
def update_subtask(subtask_id: str, payload: SubtaskUpdate, db: Session = Depends(get_db)):
    return service.update_subtask(db, subtask_id, payload)

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
def list_tags(group_id: str, db: Session = Depends(get_db)):
    return service.list_tags_by_group(db, group_id)

# ----- AI Generate Subtasks -----
@router.post("/{task_id}/generate-subtasks", response_model=GenerateSubtasksResponse)
def generate_subtasks(task_id: str, payload: GenerateSubtasksRequest, db: Session = Depends(get_db)):
    return service.generate_subtasks(db, task_id, payload)