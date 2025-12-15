from uuid import UUID
from typing import List, Optional, Literal

from sqlalchemy.orm import Session
from sqlalchemy import func, distinct

from models.task import (
    Task,
    TagGroup,
    Tag,
    TaskStatus,
)
from tasks.schemas import *

from tasks.llm import openrouter_chat
from tasks.prompts import load
import json
from fastapi import HTTPException

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
    
    # if update top-level task priority, propagate to subtasks
    if (not task.is_subtask) and ("priority" in data):
        db.query(Task).filter(
            Task.parent_id == task.id,
            Task.is_subtask.is_(True),
        ).update(
            {Task.priority: task.priority},
            synchronize_session=False,
        )

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
    tag_ids: Optional[List[UUID]] = None,
    match: Literal["any", "all"] = "any",
) -> List[Task]:
    query = db.query(Task)

    if is_subtask is not None:
        if is_subtask:
            """
            When is_subtask=True, filter tasks that don't have subtasks and subtasks
            When is_subtask=False, filter tasks
            When is_subtask is None, filter all tasks and subtasks
            """
            query = query.filter(~Task.subtasks.any())
        else:
            query = query.filter(Task.is_subtask.is_(False))
    if parent_id is not None:
        query = query.filter(Task.parent_id == parent_id)
    if status is not None:
        query = query.filter(Task.status == status)
    if category is not None:
        query = query.filter(Task.category == category)
    
    # Tag filter
    """
    tag_ids: list of UUIDs
    match="any": tasks that have at least one of the tags
    match="all": tasks that have all of the tags
    """
    if tag_ids:
        if match == "any":
            query = (
                query.join(Task.tags)
                .filter(Tag.id.in_(tag_ids))
                .distinct()
            )
        elif match == "all":
            query = (
                query.join(Task.tags)
                .filter(Tag.id.in_(tag_ids))
                .group_by(Task.id)
                .having(func.count(distinct(Tag.id)) == len(tag_ids))
            )
        else:
            # default to "any"
            query = (
                query.join(Task.tags)
                .filter(Tag.id.in_(tag_ids))
                .distinct()
            )

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
        priority=parent.priority,
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
        user_id=None,
        is_single_select=payload.is_single_select,
        allow_add_tag=payload.allow_add_tag,
    )
    db.add(group)
    db.commit()
    db.refresh(group)
    return group


def list_tag_groups(db: Session) -> List[TagGroup]:
    return db.query(TagGroup).order_by(TagGroup.created_at.asc()).all()

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
        .order_by(Tag.created_at.asc())
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

# ----- Task Categories -----
def list_task_categories(db: Session) -> List[str]:
    categories = db.query(Task.category).distinct().order_by(Task.category.asc()).all()
    return [c[0] for c in categories if c[0] is not None]

# ----- AI Generate Subtasks -----

def _build_allowed_tags_snapshot(db: Session) -> dict:
    groups = db.query(TagGroup).order_by(TagGroup.created_at.asc()).all()
    out: dict[str, list[str]] = {}
    for group in groups:
        tags = [tag.name for tag in group.tags]
        out[group.name] = tags
    return out

def _system_prompt_for_subtasks(*, allowed: dict) -> str:
    allowed_json = json.dumps(allowed, ensure_ascii=False)
    print("所有的 allowed_json:"+allowed_json)
    prompt = load("generate_subtasks_system.txt")
    return prompt.replace("{{ALLOWED_JSON}}", allowed_json)

def _normalize_subtask_proposal(raw: dict) -> dict:
    title = (raw.get("title") or "").strip()
    description = raw.get("description") or None

    est = raw.get("estimated_minutes")
    if not isinstance(est, int):
        est = None

    tags = raw.get("tags")
    if not isinstance(tags, list):
        tags = []
    
    cleaned_tags = [
        t for t in tags
        if isinstance(t, dict)
        and isinstance(t.get("group"), str)
        and isinstance(t.get("name"), str)
    ]

    return {
        "title": title[:200],
        "description": description,
        "estimated_minutes": est,
        "tags": cleaned_tags,
    }

async def generate_subtasks(
    db: Session,
    task_id: UUID,
)-> list[Task]:
    """
    Will do:
    1. Get Task.description by task_id
    2. Call AI to generate multiple subtasks + tags
    3. Save into DB
    For now, just a safe stub to avoid /docs import failure.
    """

    task = db.query(Task).filter(Task.id == task_id, Task.is_subtask.is_(False)).first()
    if not task:
        return None
    
    # 1) LLM call + parse
    allowed = _build_allowed_tags_snapshot(db)
    system = _system_prompt_for_subtasks(allowed=allowed)

    user = f"""
        使用者的大任務標題：{task.title}
        使用者的大任務描述：{task.description or ""}
        使用者規劃的大任務預計時間：{task.estimated_minutes or "無"}
    """.strip()

    # content = await openrouter_chat([
    #         {"role": "system", "content": system},
    #         {"role": "user", "content": user},
    #     ])

    content = await openrouter_chat([
        {"role": "user", "content": system + "\n\n" + user},
    ])

    print("LLM raw content:", content)
    
    # Parse JSON
    try:
        data = json.loads(content)
    except json.JSONDecodeError:
        cleaned = content.strip().removeprefix("```json").removesuffix("```").strip()
        data = json.loads(cleaned)
    
    raw_subtasks = data.get("subtasks", [])
    if not isinstance(raw_subtasks, list):
        raw_subtasks = []

    subtasks_data = [
        _normalize_subtask_proposal(s)
        for s in raw_subtasks
        if isinstance(s, dict)
    ]

    print("Parsed subtasks tags:", [s.get("tags") for s in subtasks_data])

    # 2) DB transaction: delete old, Create new Subtasks
    all_tags = db.query(Tag).join(TagGroup).all()
    tag_index: dict[tuple[str, str], Tag] = {
        (t.group.name, t.name): t for t in all_tags
    }

    created: list[Task] = []

    try:
        # delete old subtasks
        old_subtasks = db.query(Task).filter(
            Task.parent_id == task.id,
            Task.is_subtask.is_(True),
        ).all()

        for st in old_subtasks:
            st.tags.clear() # clear association first
            db.delete(st)   

        db.flush() 

        
        # create new subtasks
            
        for s in subtasks_data:
            subtask = Task(
                title=s["title"],
                description=s["description"],
                due_date=task.due_date,
                status=TaskStatus.pending,
                priority=task.priority,
                estimated_minutes=s["estimated_minutes"],
                actual_minutes=None,
                category=task.category,
                is_subtask=True,
                parent_id=task.id,
                user_id=task.user_id,
            )
            
            # attach tags
            req_tags = s["tags"]
            for item in req_tags:
                tag_obj = tag_index.get((item["group"], item["name"]))
                if tag_obj:
                    subtask.tags.append(tag_obj)
            
            db.add(subtask)
            created.append(subtask)
        
        db.commit()

    except Exception as e:
        db.rollback()
        print("Error during generate_subtasks DB transaction:", repr(e))
        raise

    db.refresh(task)
    _ = task.subtasks
    for st in task.subtasks:
        _ = st.tags

    return _attach_progress(task)

# ----- Questions for AI Regenerate Subtasks -----
async def regenerate_questions(
    db: Session,
    task_id: UUID,
    generated_subtasks: QuestionsRequest,
) -> Optional[QuestionsResponse]:
    """
    Generate 3 questions to help improve the next subtask generation
    based on the previous unsatisfactory result.
    """
    # Get task and verify it exists and is not a subtask
    task = db.query(Task).filter(Task.id == task_id, Task.is_subtask.is_(False)).first()
    if not task:
        return None

    prompt = load("regenerate_subtasks_questions.txt")
    
    # 1) Prepare ORIGINAL_TASK and GENERATED_SUBTASKS
    original_task = f"""
        使用者的大任務標題：{task.title}
        使用者的大任務描述：{task.description or ""}
        使用者的大任務類型：{task.category or "無"}
        使用者規劃的大任務預計時間(分鐘)：{task.estimated_minutes or "無"}
    """.strip()
    
    generated_subtasks_text = f"""
    已經生成的子任務列表：
    """ + "\n".join([
        f"- 子任務：{s}"
        for s in generated_subtasks
    ])

    # 2) Insert ORIGINAL_TASK and GENERATED_SUBTASKS into prompt
    prompt = prompt.replace("{{ORIGINAL_TASK}}", original_task)
    prompt = prompt.replace("{{GENERATED_SUBTASKS}}", generated_subtasks_text)

    # For debugging
    # print("Regenerate Questions Prompt:", prompt)

    # 3) LLM call
    content = await openrouter_chat([
        {"role": "user", "content": prompt},
    ])
    print("LLM raw content for regenerate questions:", content)

    return await parse_question_response(content)

async def parse_question_response(content: str) -> QuestionsResponse:
    # Parse JSON
    try:
        data = json.loads(content)
    except json.JSONDecodeError:
        cleaned = content.strip().removeprefix("```json").removesuffix("```").strip()
        data = json.loads(cleaned)
        
    raw_questions = data.get("questions", [])
    if not isinstance(raw_questions, list):
        raw_questions = []

    questions: list[Question] = []
    for q in raw_questions:
        if not isinstance(q, dict):
            continue
        question_text = q.get("question")
        suggested_answers = q.get("suggested_answers", [])
        if not isinstance(question_text, str) or not question_text.strip():
            continue
        if not isinstance(suggested_answers, list):
            suggested_answers = []
        cleaned_answers = [
            a for a in suggested_answers
            if isinstance(a, str)
        ]
        questions.append(Question(question=question_text.strip(), suggested_answers=cleaned_answers))

    return QuestionsResponse(questions=questions)


# ----- Ensure Default System Tag Groups -----
DEFAULT_SYSTEM_GROUPS = ["Tools", "Mode", "Location","Interruptibility"]
DEFAULT_SYSTEM_TAGS = {
    "Tools": ["Phone", "Computer", "iPad", "Textbook"],
    "Mode": ["Relax", "Focus", "Efficiency"],
    "Location": ["Home", "Classroom", "Library", "None"],
    "Interruptibility": ["Interruptible", "Not Interruptible"],
}

def ensure_default_tag_groups(db: Session):
    SINGLE_SELECT_GROUPS = {"Mode","Interruptibility"}

    # ensure default groups
    group_map: dict[str, TagGroup] = {}
    for name in DEFAULT_SYSTEM_GROUPS:
        group = (
            db.query(TagGroup)
            .filter(TagGroup.name == name, TagGroup.type == "system")
            .first()
        )
        if not group:
            group = TagGroup(
                name=name,
                type="system",
            )
            db.add(group)
            db.flush()
        
        if name in SINGLE_SELECT_GROUPS:
            group.is_single_select = True
            group.allow_add_tag = False
        else:
            group.is_single_select = False
            group.allow_add_tag = True

        group_map[name] = group
    
    # ensure default tags
    for group_name, tag_names in DEFAULT_SYSTEM_TAGS.items():
        group = group_map.get(group_name)
        if not group:
            continue
        for tag_name in tag_names:
            exists = (
                db.query(Tag)
                .filter(Tag.tag_group_id == group.id, Tag.name == tag_name)
                .first()
            )
            if not exists:
                db.add(
                    Tag(
                        name=tag_name,
                        tag_group_id=group.id,
                        is_system=True,
                    )
                )

    db.commit()