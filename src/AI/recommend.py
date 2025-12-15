# src/AI/recommend.py
import os
import json
import re
import logging
from typing import List, Dict, Any
from collections import defaultdict

import requests
from sqlalchemy import text

logger = logging.getLogger("TaskRecommender")
if not logging.getLogger().handlers:
    logging.basicConfig(level=logging.INFO)

# =========================
# Scoring weights (backend)
# =========================
SCORE_WEIGHTS = {
    "time_score": 4,
    "place_score": 2,
    "mode_score": 2,
    "tool_score": 10,
    "interruptible": 4,
    "deadline": 4,
}

# =========================
# Ollama config
# =========================
# NOTE:
# - Docker Desktop / WSL 通常用 host.docker.internal
# - 若你不是 Docker Desktop，改用你 host 的 IP（例如 172.17.0.1）
OLLAMA_URL = os.getenv("OLLAMA_URL", "http://host.docker.internal:11434/api/generate")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3.2:latest")
OLLAMA_TIMEOUT = float(os.getenv("OLLAMA_TIMEOUT", "120"))
OLLAMA_TEMPERATURE = float(os.getenv("OLLAMA_TEMPERATURE", "0.2"))


def _strip_code_fence(s: str) -> str:
    s = (s or "").strip()
    if s.startswith("```"):
        s = re.sub(r"^```[a-zA-Z]*\n?", "", s)
        s = re.sub(r"\n?```$", "", s)
    return s.strip()


def _extract_json_obj(text: str) -> Any:
    """
    Ollama 有時會多吐一些字，這邊盡量把 JSON 挖出來。
    """
    text = _strip_code_fence(text)
    # 1) 直接當 JSON
    try:
        return json.loads(text)
    except Exception:
        pass

    # 2) 抓最外層 {...}
    m = re.search(r"\{.*\}", text, flags=re.S)
    if not m:
        raise ValueError(f"LLM output has no JSON object: {text[:200]}")
    return json.loads(m.group(0))


def call_ollama(prompt: str) -> str:
    payload = {
        "model": OLLAMA_MODEL,
        "prompt": prompt,
        "stream": False,
        "options": {
            "temperature": OLLAMA_TEMPERATURE,
        },
    }
    r = requests.post(OLLAMA_URL, json=payload, timeout=OLLAMA_TIMEOUT)
    r.raise_for_status()
    data = r.json()
    # Ollama /api/generate 通常回 {"response": "..."}
    return data.get("response", "") or ""


class TaskRecommender:
    def __init__(self, db_session, *args, **kwargs):
        self.db = db_session
        self._llm_debug = {"prompt": None, "response": None, "exception": None}

    def get_llm_debug(self):
        return dict(self._llm_debug)

    # =========================
    # 0) Load tasks
    # =========================
    def load_tasks_with_tags(self) -> List[Dict[str, Any]]:
        """
        盡量把 deadline（due_date）也帶出來，讓 deadline_score 有資料可用。
        如果你 DB 沒有 due_date 欄位，會自動 fallback。
        """
        sql_with_due = text("""
        SELECT
          t.id                AS task_id,
          t.title             AS title,
          t.estimated_minutes AS estimated_minutes,
          t.priority          AS priority,
          t.parent_id         AS parent_id,
          t.is_subtask        AS is_subtask,
          t.due_date          AS due_date,
          tg.name             AS tag_group,
          tag.name            AS tag_name
        FROM tasks t
        LEFT JOIN task_tags tt ON tt.task_id = t.id
        LEFT JOIN tags tag ON tag.id = tt.tag_id
        LEFT JOIN tag_groups tg ON tg.id = tag.tag_group_id
        WHERE t.status = 'pending'
        ORDER BY t.id;
        """)

        sql_no_due = text("""
        SELECT
          t.id                AS task_id,
          t.title             AS title,
          t.estimated_minutes AS estimated_minutes,
          t.priority          AS priority,
          t.parent_id         AS parent_id,
          t.is_subtask        AS is_subtask,
          NULL                AS due_date,
          tg.name             AS tag_group,
          tag.name            AS tag_name
        FROM tasks t
        LEFT JOIN task_tags tt ON tt.task_id = t.id
        LEFT JOIN tags tag ON tag.id = tt.tag_id
        LEFT JOIN tag_groups tg ON tg.id = tag.tag_group_id
        WHERE t.status = 'pending'
        ORDER BY t.id;
        """)

        try:
            rows = self.db.execute(sql_with_due).fetchall()
        except Exception:
            rows = self.db.execute(sql_no_due).fetchall()

        tasks: Dict[str, Any] = {}
        for r in rows:
            tid = str(r.task_id)
            if tid not in tasks:
                tasks[tid] = {
                    "id": tid,
                    "title": r.title,
                    "estimated_minutes": r.estimated_minutes,
                    "priority": r.priority,
                    "parent_id": str(r.parent_id) if r.parent_id else None,
                    "is_subtask": bool(r.is_subtask),
                    "due_date": (str(r.due_date) if r.due_date else None),
                    "tags": defaultdict(list),
                }
            if r.tag_group and r.tag_name:
                tasks[tid]["tags"][r.tag_group].append(r.tag_name)

        for t in tasks.values():
            t["tags"] = dict(t["tags"])

        return list(tasks.values())

    # =========================
    # 1) ONE prompt batch scoring
    # =========================
    def build_scoring_prompt(
        self,
        tasks: List[Dict[str, Any]],
        user_context: Dict[str, Any],
        user_profile: Dict[str, Any],
    ) -> str:
        # 這段就是你要的「整塊 prompt，不分割、一次塞完 tasks」
        return f"""
You are a scoring model.
Return ONLY valid JSON. No explanation. No markdown.

You will score EACH task independently on these dimensions (integer only: 0, 1, or 2):
- time_score: how well task estimated_minutes matches USER_CONTEXT.available_minutes (closer = higher)
- place_score: task place tags vs USER_CONTEXT.current_place (match = higher; missing info => 0)
- mode_score: task mode tags vs USER_CONTEXT.mode (must match to score; missing info => 0)
- tool_score: task required tool tags vs USER_CONTEXT.tools (user must have it; missing info => 0)
- interruptible: if task explicitly says it can be interrupted (missing info => 0)
- deadline: if task due_date is close/urgent (missing info => 0)

Important rule:
- If information is missing / noselect / unclear, give 0 (do NOT guess).

INPUTS (JSON):
USER_CONTEXT:
{json.dumps(user_context, ensure_ascii=False)}

USER_PROFILE:
{json.dumps(user_profile, ensure_ascii=False)}

TASKS:
{json.dumps(tasks, ensure_ascii=False)}

Output STRICT JSON with this exact schema:
{{
  "scores": [
    {{
      "task_id": "uuid",
      "time_score": 0,
      "place_score": 0,
      "mode_score": 0,
      "tool_score": 0,
      "interruptible": 0,
      "deadline": 0
    }}
  ]
}}
""".strip()

    def score_tasks_batch(
        self,
        tasks: List[Dict[str, Any]],
        user_context: Dict[str, Any],
        user_profile: Dict[str, Any],
    ) -> List[Dict[str, Any]]:
        prompt = self.build_scoring_prompt(tasks, user_context, user_profile)
        self._llm_debug = {"prompt": prompt, "response": None, "exception": None}
        logger.info("Calling OLLAMA (model=%s, prompt len=%d)", OLLAMA_MODEL, len(prompt))

        try:
            raw = call_ollama(prompt)
            self._llm_debug["response"] = raw
            parsed = _extract_json_obj(raw)
            scores = parsed.get("scores", [])
            if not isinstance(scores, list):
                return []
            return scores
        except Exception as e:
            self._llm_debug["exception"] = str(e)
            logger.exception("Ollama scoring failed")
            return []

    # =========================
    # 2) Backend rank + deterministic reasons
    # =========================
    def _clamp_0_2(self, v: Any) -> int:
        try:
            iv = int(v)
        except Exception:
            return 0
        return 0 if iv < 0 else (2 if iv > 2 else iv)

    def _build_reason(self, task: Dict[str, Any], s: Dict[str, Any], user_context: Dict[str, Any]) -> str:
        parts = []
        avail = user_context.get("available_minutes")
        if self._clamp_0_2(s.get("time_score")) == 2:
            parts.append(f"時間很貼合（任務約 {task.get('estimated_minutes')} 分鐘 / 你可用 {avail} 分鐘）")
        elif self._clamp_0_2(s.get("time_score")) == 1:
            parts.append(f"時間還算合理（任務約 {task.get('estimated_minutes')} 分鐘）")

        if self._clamp_0_2(s.get("tool_score")) == 2:
            parts.append("工具符合（你現在有可用工具）")

        if self._clamp_0_2(s.get("mode_score")) == 2:
            parts.append("模式符合你目前狀態")

        if self._clamp_0_2(s.get("place_score")) == 2:
            parts.append("地點條件相符")

        if self._clamp_0_2(s.get("interruptible")) == 2:
            parts.append("可中斷，不怕被打斷")

        if self._clamp_0_2(s.get("deadline")) == 2:
            parts.append("截止壓力高，現在做最划算")
        elif self._clamp_0_2(s.get("deadline")) == 1:
            parts.append("有截止風險，先處理比較安心")

        if not parts:
            # 全 0 的情況：至少給一個乾淨理由
            return "目前資訊不足（任務缺少標籤/條件），但仍可作為備選。"

        return "；".join(parts) + "。"

    def rank(self, user_context: Dict[str, Any]) -> Dict[str, Any]:
        user_profile = user_context.get("base_profile", {})
        tasks = self.load_tasks_with_tags()

        logger.info("Total tasks loaded: %d", len(tasks))
        if not tasks:
            return {"recommended_tasks": [], "debug": {"scored_count": 0}}

        scores = self.score_tasks_batch(tasks, user_context, user_profile)
        task_map = {t["id"]: t for t in tasks}

        scored_tasks = []
        for s in scores:
            tid = s.get("task_id")
            if tid not in task_map:
                continue

            # clamp scores
            s2 = {
                "task_id": tid,
                "time_score": self._clamp_0_2(s.get("time_score")),
                "place_score": self._clamp_0_2(s.get("place_score")),
                "mode_score": self._clamp_0_2(s.get("mode_score")),
                "tool_score": self._clamp_0_2(s.get("tool_score")),
                "interruptible": self._clamp_0_2(s.get("interruptible")),
                "deadline": self._clamp_0_2(s.get("deadline")),
            }

            final_score = sum(s2[k] * SCORE_WEIGHTS[k] for k in SCORE_WEIGHTS)

            scored_tasks.append({
                "task": task_map[tid],
                "scores": s2,
                "final_score": round(float(final_score), 4),
            })

        logger.info("Total tasks scored: %d", len(scored_tasks))
        if not scored_tasks:
            return {
                "recommended_tasks": [],
                "debug": {"scored_count": 0, "llm": self.get_llm_debug()},
            }

        scored_tasks.sort(key=lambda x: x["final_score"], reverse=True)
        top_tasks = scored_tasks[:4]

        recommended = []
        for item in top_tasks:
            t = item["task"]
            s = item["scores"]
            recommended.append({
                "task_id": t["id"],
                "reason": self._build_reason(t, s, user_context),
            })

        return {
            "recommended_tasks": recommended,
            "debug": {
                "scored_count": len(scored_tasks),
                "top_tasks": [
                    {"id": x["task"]["id"], "title": x["task"]["title"], "final_score": x["final_score"], "scores": x["scores"]}
                    for x in top_tasks
                ],
                "llm": self.get_llm_debug(),
                "ollama": {"url": OLLAMA_URL, "model": OLLAMA_MODEL},
            },
        }
