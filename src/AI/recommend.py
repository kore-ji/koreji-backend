# src/ai/recommend.py

import json
from typing import List, Dict, Any
from collections import defaultdict
from sqlalchemy import text
from .Client import call_llm


# ====================================================
# Backend-controlled scoring weights
# ====================================================
SCORE_WEIGHTS = {
    "time_score": 4,
    "place_score": 2,
    "mode_score": 2,
    "tool_score": 10,
    "interruptible": 4,
    "deadline": 4,
}


class TaskRecommender:
    def __init__(self, db):
        """
        db: SQLAlchemy Session
        """
        self.db = db

    # ====================================================
    # 0. Load ALL tasks with tags (DB layer)
    # ====================================================
    def load_tasks_with_tags(self) -> List[Dict[str, Any]]:
        """
        Load ALL pending tasks from database with tags.
        No filtering, no scoring.
        """

        sql = text("""
        SELECT
          t.id                AS task_id,
          t.title             AS title,
          t.estimated_minutes AS estimated_minutes,
          t.priority          AS priority,
          t.parent_id         AS parent_id,
          t.is_subtask        AS is_subtask,
          tg.name             AS tag_group,
          tag.name            AS tag_name
        FROM tasks t
        LEFT JOIN task_tags tt ON tt.task_id = t.id
        LEFT JOIN tags tag ON tag.id = tt.tag_id
        LEFT JOIN tag_groups tg ON tg.id = tag.tag_group_id
        WHERE t.status = 'pending'
        ORDER BY t.id;
        """)

        rows = self.db.execute(sql).fetchall()

        tasks = {}

        for r in rows:
            task_id = str(r.task_id)

            if task_id not in tasks:
                tasks[task_id] = {
                    "id": task_id,
                    "title": r.title,
                    "estimated_minutes": r.estimated_minutes,
                    "priority": r.priority,
                    "parent_id": str(r.parent_id) if r.parent_id else None,
                    "is_subtask": r.is_subtask,
                    "tags": defaultdict(list),
                }

            if r.tag_group and r.tag_name:
                tasks[task_id]["tags"][r.tag_group].append(r.tag_name)

        # defaultdict → normal dict
        for task in tasks.values():
            task["tags"] = dict(task["tags"])

        return list(tasks.values())

    # ====================================================
    # 1. LLM SCORING (dimension-only)
    # ====================================================
    def score_task(
        self,
        task: Dict[str, Any],
        user_context: Dict[str, Any],
        user_profile: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Ask LLM to score ONE task on fixed dimensions.
        LLM must NOT compute final_score.
        """

        prompt = f"""
You are a scoring model.
Return ONLY valid JSON. No explanation.

Dimensions:
我會告訴你要怎麼評分每個 Tag，如果該項目說明或者選擇 noselect，就給 0 分。
- 時間適配度 : 時間與使用者當前可用時間的時間越相近越高分。
- 地點適配度 : 任務地點與使用者當前地點越接近越高分。
- 模式適配度 : 任務模式與使用者相同才給分。
- 中斷 : 如果任務是可以被中斷的，請給予滿分。
- 截止期限 : 如果任務越接近截止期限，請給予越高分。
- 可用工具適配度 : 只有使用者擁有才給滿分。

TASK:
{json.dumps(task, ensure_ascii=False)}

USER_CONTEXT:
{json.dumps(user_context, ensure_ascii=False)}

USER_PROFILE:
{json.dumps(user_profile, ensure_ascii=False)}

Return format:
{{
  "time_score": -2-2,
  "place_score": -2-2,
  "mode_score": -2-2,
  "tool_score": -2-2,
  "interruptible": -2-2,
  "deadline": -2-2
}}
"""

        raw = call_llm(prompt)
        scores = json.loads(raw)

        final_score = sum(
            scores.get(key, 0) * weight
            for key, weight in SCORE_WEIGHTS.items()
        )

        return {
            "task": task,
            "scores": scores,
            "final_score": round(final_score, 4),
        }

    # ====================================================
    # 2. Backend ranking (deterministic)
    # ====================================================
    def rank(self, user_context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Full pipeline:
        DB → load → score → sort → explain
        """

        user_profile = user_context.get("base_profile", {})

        tasks = self.load_tasks_with_tags()

        scored_tasks = []
        for task in tasks:
            try:
                scored_tasks.append(
                    self.score_task(task, user_context, user_profile)
                )
            except Exception:
                continue

        if not scored_tasks:
            return {"recommended_tasks": []}

        scored_tasks.sort(
            key=lambda x: x["final_score"],
            reverse=True
        )

        top_tasks = scored_tasks[:4]

        return self.generate_reasons(top_tasks, user_context)

    # ====================================================
    # 3. LLM explanation (post-hoc only)
    # ====================================================
    def generate_reasons(
        self,
        ranked_tasks: List[Dict[str, Any]],
        user_context: Dict[str, Any],
    ) -> Dict[str, Any]:

        prompt = f"""
You are a task explanation model.
The ranking is FINAL.
Do NOT score or reorder tasks.

USER_CONTEXT:
{json.dumps(user_context, ensure_ascii=False)}

RANKED_TASKS:
{json.dumps(
    [
        {
            "rank": idx + 1,
            "task_id": item["task"]["id"],
            "title": item["task"]["title"],
        }
        for idx, item in enumerate(ranked_tasks)
    ],
    ensure_ascii=False
)}

Output STRICT JSON only:
{{
  "recommended_tasks": [
    {{
      "task_id": "task_xxx",
      "reason": "Explain naturally why this task fits now and why it ranks here."
    }}
  ]
}}
"""

        raw = call_llm(prompt)

        try:
            return json.loads(raw)
        except Exception:
            return {
                "error": "Invalid JSON from explanation model",
                "raw": raw,
            }
