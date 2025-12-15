# src/AI/testllm.py
import json
import re
from sqlalchemy import text

from database import get_db
from AI.prompt import TaskRecommender
from AI.client import call_llm


def load_tasks_from_db(db):
    sql = text("""
    SELECT
        t.id,
        t.title,
        t.estimated_minutes,
        t.due_date,
        tg.name AS tag_group,
        tag.name AS tag_name
    FROM tasks t
    LEFT JOIN task_tags tt ON tt.task_id = t.id
    LEFT JOIN tags tag ON tag.id = tt.tag_id
    LEFT JOIN tag_groups tg ON tg.id = tag.tag_group_id
    WHERE t.status = 'pending'
    ORDER BY t.created_at;
    """)

    rows = db.execute(sql).fetchall()

    tasks = {}
    for r in rows:
        tid = str(r.id)
        if tid not in tasks:
            tasks[tid] = {
                "task_id": tid,
                "title": r.title,
                "estimated_minutes": r.estimated_minutes,
                "due_date": str(r.due_date) if r.due_date else None,
                "tags": {},
            }
        if r.tag_group and r.tag_name:
            tasks[tid]["tags"].setdefault(r.tag_group, []).append(r.tag_name)

    return list(tasks.values())


def _extract_json(text: str):
    # 允許 ```json ... ``` 或直接 JSON
    s = (text or "").strip()
    s = re.sub(r"^```json\s*", "", s)
    s = re.sub(r"^```\s*", "", s)
    s = re.sub(r"\s*```$", "", s)
    m = re.search(r"\{.*\}", s, flags=re.S)
    if not m:
        raise ValueError("LLM output is not JSON")
    return json.loads(m.group(0))


def get_recommendation_from_db_and_llm(db, user_current: dict):
    """Load pending tasks from DB, build prompt via `TaskRecommender`, call LLM and return parsed JSON.

    Args:
        db: SQLAlchemy connection/session
        user_current: dict with keys `available_minutes`, `current_place`, `mode`, `tools`

    Returns:
        dict: parsed JSON from LLM
    """
    tasks = load_tasks_from_db(db)

    payload = {
        "user_current_input": user_current,
        "user_long_term_profile": {},
        "candidate_tasks_after_sql_filtering": tasks,
        "exclude_list": [],
    }

    recommender = TaskRecommender()
    prompt = recommender.build_prompt(tasks=tasks, user_context=payload)

    raw = call_llm(prompt)
    return _extract_json(raw)
