from pydantic import BaseModel
from typing import List

class RecommendRequest(BaseModel):
    time: int
    mode: str
    place: str
    tool: str  # comma-separated values e.g. "phone, computer"

class RecommendedTask(BaseModel):
    task_id: str
    task_name: str
    reason: str

class RecommendResponse(RecommendRequest):
    recommended_tasks: List[RecommendedTask]

# ----- Regenerate recommendation Questions -----
class QuestionsResponse(RecommendRequest):
    questions: List[str]

class RegenerateRequest(RecommendRequest):
    questions: List[str]
    answers: List[str]