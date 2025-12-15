from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
import json

from AI.schema import *
from AI.client import call_llm
from models.task import Task, Tag, TagGroup, TaskStatus
from AI.prompts import load
from utils.llm_utils import parse_question_response


def _build_tasks_context(db: Session) -> str:
    """Build a formatted string of all pending tasks for LLM context."""
    tasks = db.query(Task).filter(
        Task.status == TaskStatus.pending,
        Task.is_subtask.is_(False)
    ).all()
    
    if not tasks:
        return "目前沒有待處理的任務。"
    
    lines = ["目前可用的任務列表："]
    for idx, task in enumerate(tasks, 1):
        # Force load tags
        _ = task.tags
        tag_names = ", ".join([t.name for t in task.tags]) if task.tags else "無"
        
        lines.append(f"{idx}. {task.title}")
        lines.append(f"   分類：{task.category or '無'}")
        lines.append(f"   描述：{task.description or '無'}")
        lines.append(f"   預估時間：{task.estimated_minutes or '無'} 分鐘")
        lines.append(f"   標籤：{tag_names}")
    
    return "\n".join(lines)


async def regenerate_questions(
    db: Session,
    current_context: RecommendRequest,
) -> Optional[QuestionsResponse]:
    """
    Generate 3 questions to help understand why user is unsatisfied
    with the current recommendation results.
    
    Similar to tasks regenerate_questions, but for recommendation refinement.
    """
    
    # 1) Load prompt template
    try:
        prompt_template = load("regenerate_recommendation_questions.txt")
    except FileNotFoundError:
        return None  # Prompt template missing
    
    # 2) Build user context string
    user_context = f"""
可用時間：{current_context.time} 分鐘
當前模式：{current_context.mode}
當前地點：{current_context.place or "未指定"}
可用工具：{", ".join(current_context.tool) if current_context.tool else "未指定"}
    """.strip()
    
    # 3) Build available tasks context
    available_tasks = _build_tasks_context(db)
    
    # 4) Replace placeholders in prompt
    prompt = prompt_template.replace("{{USER_CONTEXT}}", user_context)
    prompt = prompt.replace("{{AVAILABLE_TASKS}}", available_tasks)
    
    # 5) Call LLM
    content = call_llm(prompt)
    print("LLM raw content for regenerate recommendation questions:", content)
    
    # 6) Parse response
    result = parse_question_response(content)
    return QuestionsResponse(questions=result["questions"])


async def regenerate_recommendations(
    db: Session,
    current_context: RecommendRequest,
    feedback: RegenerateRecommendationRequest,
) -> Optional[List[Task]]:
    """
    Regenerate task recommendations based on user feedback.
    
    Takes the user's answers to refinement questions and generates
    improved recommendations that better match their requirements.
    """
    
    # 1) Load previous recommendation results (if any stored in session/cache)
    # For now, we'll fetch current pending tasks as baseline
    previous_recommendations = db.query(Task).filter(
        Task.status == TaskStatus.pending,
        Task.is_subtask.is_(False)
    ).limit(4).all()
    
    # Force load tags
    for task in previous_recommendations:
        _ = task.tags
    
    # Format previous recommendations
    previous_recs_text = "上次推薦的任務：\n"
    if previous_recommendations:
        for idx, task in enumerate(previous_recommendations, 1):
            tag_names = ", ".join([t.name for t in task.tags]) if task.tags else "無"
            previous_recs_text += f"{idx}. {task.title}\n"
            previous_recs_text += f"   預估時間：{task.estimated_minutes or '無'} 分鐘\n"
            previous_recs_text += f"   標籤：{tag_names}\n"
    else:
        previous_recs_text += "（尚未有推薦記錄）\n"
    
    # 2) Load prompt template
    try:
        prompt_template = load("regenerate_recommendations.txt")
    except FileNotFoundError:
        return None  # Prompt template missing
    
    # 3) Build user context
    user_context = f"""
可用時間：{current_context.time} 分鐘
當前模式：{current_context.mode}
當前地點：{current_context.place or "未指定"}
可用工具：{", ".join(current_context.tool) if current_context.tool else "未指定"}
    """.strip()
    
    # 4) Build feedback context from Q&A pairs
    feedback_context = ""
    for i, (question, answer) in enumerate(zip(feedback.questions, feedback.answers), 1):
        feedback_context += f"{i}. {question}\n   回答：{answer}\n"
    
    # 5) Build available tasks context
    available_tasks = _build_tasks_context(db)
    
    # 6) Replace placeholders
    prompt = prompt_template.replace("{{USER_CONTEXT}}", user_context)
    prompt = prompt.replace("{{PREVIOUS_RECOMMENDATIONS}}", previous_recs_text)
    prompt = prompt.replace("{{FEEDBACK}}", feedback_context)
    prompt = prompt.replace("{{AVAILABLE_TASKS}}", available_tasks)
    
    # 7) Call LLM
    content = call_llm(prompt)
    print("LLM raw content for regenerate recommendations:", content)
    
    # 8) Parse JSON response
    try:
        data = json.loads(content)
    except json.JSONDecodeError:
        cleaned = content.strip().removeprefix("```json").removesuffix("```").strip()
        data = json.loads(cleaned)
    
    recommended_tasks = data.get("recommended_tasks", [])
    if not isinstance(recommended_tasks, list):
        return []
    
    # 9) Fetch actual tasks from DB based on LLM recommendations
    result_tasks = []
    for rec in recommended_tasks:
        if not isinstance(rec, dict):
            continue
        task_id = rec.get("task_id")
        if not task_id:
            continue
        
        task = db.query(Task).filter(Task.id == task_id).first()
        if task:
            _ = task.tags  # Force load tags
            result_tasks.append(task)
    
    return result_tasks[:4]  # Return top 4
