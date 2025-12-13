from uuid import UUID
from typing import List, Optional

from sqlalchemy.orm import Session

from models.task import (
    Task,
    TagGroup,
    Tag,
    TaskStatus,
)
from tasks.schemas import (
    TaskCreate,
    TaskUpdate,
    SubtaskCreate,
    SubtaskUpdate,
    TagGroupCreate,
    TagGroupUpdate,
    TagCreate,
    TagUpdate,
    UpdateTaskTagsRequest,
    GenerateSubtasksRequest,
)


# ----- Calculus Task progress -----
def _compute_task_progress(task: Task) -> float:
    if task.is_subtask:
        return 0.0
    if not task.subtasks:
        return 0.0

    total = len(task.subtasks)
    completed = sum(
        1 for s in task.subtasks if s.status == TaskStatus.completed
    )
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
        status=payload.status,
        priority=payload.priority,
        estimated_minutes=payload.estimated_minutes,
        actual_minutes=payload.actual_minutes,
        is_subtask=False,
        parent_id=None,
        user_id=None,
    )
    db.add(task)
    db.commit()
    db.refresh(task)
    return _attach_progress(task)


def get_task(db: Session, task_id: str) -> Optional[Task]:
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        return None
    # 觸發載入 subtasks/tags
    _ = task.subtasks
    _ = task.tags
    return _attach_progress(task)

def update_task(db: Session, task_id: str, payload: TaskUpdate) -> Optional[Task]:
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        return None

    data = payload.dict(exclude_unset=True)
    for key, value in data.items():
        setattr(task, key, value)

    db.commit()
    db.refresh(task)
    return _attach_progress(task)

# ----- Task List / Subtask List -----
def list_tasks(
    db: Session,
    *,
    is_subtask: Optional[bool] = None,
    parent_id: Optional[UUID] = None,
    status: Optional[TaskStatus] = None,
    category: Optional[str] = None,
) -> List[Task]:
    query = db.query(Task)

    if is_subtask:
        # When is_subtask=True, include tasks that don't have subtasks
        query = query.filter(~Task.subtasks.any())
    if parent_id is not None:
        query = query.filter(Task.parent_id == parent_id)
    if status is not None:
        query = query.filter(Task.status == status)
    if category is not None:
        query = query.filter(Task.category == category)

    tasks = query.order_by(Task.due_date, Task.created_at).all()

    for t in tasks:
        if not t.is_subtask:
            _attach_progress(t)
    return tasks


def list_subtasks_for_task(db: Session, task_id: UUID) -> Optional[List[Task]]:
    parent = db.query(Task).filter(Task.id == task_id, Task.is_subtask.is_(False)).first()
    if not parent:
        return None
    return list(parent.subtasks)


# ----- Subtask -----
def create_subtask(db: Session, payload: SubtaskCreate) -> Task:
    parent = db.query(Task).filter(
        Task.id == payload.task_id,
        Task.is_subtask.is_(False),
    ).first()
    if not parent:
        return None

    subtask = Task(
        title=payload.title,
        description=payload.description,
        due_date=payload.due_date or parent.due_date,
        status=payload.status,
        priority=payload.priority,
        estimated_minutes=payload.estimated_minutes,
        actual_minutes=payload.actual_minutes,
        category=parent.category,
        is_subtask=True,
        parent_id=parent.id,
        user_id=parent.user_id,
    )
    db.add(subtask)
    db.commit()
    db.refresh(subtask)
    return subtask


# def get_subtask(db: Session, subtask_id: str) -> Optional[Subtask]:
#     return db.query(Subtask).filter(Subtask.id == uuid.UUID(subtask_id)).first()


def update_subtask(
    db: Session,
    subtask_id: str,
    payload: SubtaskUpdate,
) -> Optional[Task]:
    subtask = db.query(Task).filter(
        Task.id == subtask_id,
        Task.is_subtask.is_(True),
    ).first()
    if not subtask:
        return None

    data = payload.dict(exclude_unset=True)
    for key, value in data.items():
        setattr(subtask, key, value)

    db.commit()
    db.refresh(subtask)
    return subtask


# ----- Tag Group & Tag -----
def create_tag_group(db: Session, payload: TagGroupCreate) -> TagGroup:
    group = TagGroup(
        name=payload.name,
        type="custom",     # system we use seed build
        is_system=False,
    )
    db.add(group)
    db.commit()
    db.refresh(group)
    return group


def list_tag_groups(db: Session) -> List[TagGroup]:
    return db.query(TagGroup).order_by(TagGroup.name).all()

def update_tag_group(db: Session, group_id: UUID, payload: TagGroupUpdate) -> Optional[TagGroup]:
    group = db.query(TagGroup).filter(TagGroup.id == group_id).first()
    if not group:
        return None

    data = payload.dict(exclude_unset=True)
    for key, value in data.items():
        setattr(group, key, value)

    db.commit()
    db.refresh(group)
    return group


def create_tag(db: Session, payload: TagCreate) -> Tag:
    tag = Tag(
        name=payload.name,
        tag_group_id=payload.tag_group_id,
        is_system=False,
    )
    db.add(tag)
    db.commit()
    db.refresh(tag)
    return tag


def update_tag(db: Session, tag_id: UUID, payload: TagUpdate) -> Optional[Tag]:
    tag = db.query(Tag).filter(Tag.id == tag_id).first()
    if not tag:
        return None

    data = payload.dict(exclude_unset=True)
    for key, value in data.items():
        setattr(tag, key, value)

    db.commit()
    db.refresh(tag)
    return tag


def list_tags_by_group(db: Session, group_id: UUID) -> List[Tag]:
    return (
        db.query(Tag)
        .filter(Tag.tag_group_id == group_id)
        .order_by(Tag.name)
        .all()
    )

# ----- task <-> tags -----
def update_task_tags(db: Session, task_id: UUID, payload: UpdateTaskTagsRequest) -> Optional[Task]:
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        return None

    task.tags.clear()

    if payload.tag_ids:
        tags = db.query(Tag).filter(Tag.id.in_(payload.tag_ids)).all()
        task.tags.extend(tags)

    db.commit()
    db.refresh(task)
    return _attach_progress(task)


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

# ----- Ensure Default System Tag Groups -----
DEFAULT_SYSTEM_GROUPS = ["Tools", "Attention", "Location"]

def ensure_default_tag_groups(db: Session):
    for name in DEFAULT_SYSTEM_GROUPS:
        exists = (
            db.query(TagGroup)
            .filter(TagGroup.name == name, TagGroup.type == "system")
            .first()
        )
        if not exists:
            group = TagGroup(
                name=name,
                type="system",
                is_system=True,
            )
            db.add(group)
    db.commit()