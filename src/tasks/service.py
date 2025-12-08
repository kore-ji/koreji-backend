import uuid
from typing import List, Optional

from sqlalchemy.orm import Session

from models.task import (
    Task,
    Subtask,
    TagGroup,
    Tag,
    SubtaskStatus,
)
from tasks.schemas import (
    TaskCreate,
    TaskUpdate,
    SubtaskCreate,
    SubtaskUpdate,
    TagGroupCreate,
    TagCreate,
    GenerateSubtasksRequest,
)


# ----- Calculus Task progress -----
def _compute_task_progress(task: Task) -> float:
    if not task.subtasks:
        return 0.0
    total = len(task.subtasks)
    completed = sum(1 for s in task.subtasks if s.status == SubtaskStatus.completed)
    return completed / total


def _attach_progress(task: Task) -> Task:
    task.progress = _compute_task_progress(task)
    return task


# ----- Task -----

def create_task(db: Session, payload: TaskCreate) -> Task:
    task = Task(
        title=payload.title,
        description=payload.description,
        category=payload.category,
        due_date=payload.due_date,
        user_id=None,
    )
    db.add(task)
    db.commit()
    db.refresh(task)
    return _attach_progress(task)


def get_task(db: Session, task_id: str) -> Optional[Task]:
    task = db.query(Task).filter(Task.id == uuid.UUID(task_id)).first()
    if not task:
        return None
    _ = task.subtasks
    return _attach_progress(task)


def update_task(db: Session, task_id: str, payload: TaskUpdate) -> Optional[Task]:
    task = db.query(Task).filter(Task.id == uuid.UUID(task_id)).first()
    if not task:
        return None

    data = payload.dict(exclude_unset=True)
    for field, value in data.items():
        setattr(task, field, value)

    db.commit()
    db.refresh(task)
    return _attach_progress(task)


# ----- Subtask -----
def create_subtask(db: Session, payload: SubtaskCreate) -> Subtask:
    subtask = Subtask(
        task_id=payload.task_id,
        title=payload.title,
        description=payload.description,
        priority=payload.priority,
        status=payload.status,
        estimated_minutes=payload.estimated_minutes,
    )
    db.add(subtask)
    db.commit()
    db.refresh(subtask)
    return subtask


def get_subtask(db: Session, subtask_id: str) -> Optional[Subtask]:
    return db.query(Subtask).filter(Subtask.id == uuid.UUID(subtask_id)).first()


def update_subtask(db: Session, subtask_id: str, payload: SubtaskUpdate) -> Optional[Subtask]:
    subtask = db.query(Subtask).filter(Subtask.id == uuid.UUID(subtask_id)).first()
    if not subtask:
        return None

    data = payload.dict(exclude_unset=True)
    for field, value in data.items():
        setattr(subtask, field, value)

    db.commit()
    db.refresh(subtask)
    return subtask


# ----- Tag Group & Tag -----
def create_tag_group(db: Session, payload: TagGroupCreate) -> TagGroup:
    group = TagGroup(name=payload.name)
    db.add(group)
    db.commit()
    db.refresh(group)
    return group


def list_tag_groups(db: Session) -> List[TagGroup]:
    return db.query(TagGroup).order_by(TagGroup.name).all()


def create_tag(db: Session, payload: TagCreate) -> Tag:
    tag = Tag(
        name=payload.name,
        tag_group_id=payload.tag_group_id,
    )
    db.add(tag)
    db.commit()
    db.refresh(tag)
    return tag


def list_tags_by_group(db: Session, group_id: str) -> List[Tag]:
    return (
        db.query(Tag)
        .filter(Tag.tag_group_id == uuid.UUID(group_id))
        .order_by(Tag.name)
        .all()
    )


# ----- AI Generate Subtasks -----
def generate_subtasks(
    db: Session,
    task_id: UUID,
    payload: GenerateSubtasksRequest,
):
    """
    Will do:
    1. Get Task.description by task_id
    2. Call AI to generate multiple subtasks + tags
    3. Save into DB
    For now, just a safe stub to avoid /docs import failure.
    """

    task = get_task(db, task_id)
    if not task:
        return {"subtasks": []}

    # For now, send back the existing subtasks; will  modify them once actually implement AI.
    return {"subtasks": list(task.subtasks)}
