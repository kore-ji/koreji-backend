from pydantic import BaseModel
from typing import List, Optional
from tasks.schemas import TaskResponse

class RecommendRequest(BaseModel):
    time: int
    mode: str 
    place: Optional[str] = None
    tool: List[str] = []

class Recommendation(BaseModel):
    task_name: str
    reason: str

class RecommendResponse(RecommendRequest):
    recommended_tasks: List[Recommendation]

# ----- Regenerate recommendation Questions -----
class QuestionsResponse(BaseModel):
    questions: List[str]

class RegenerateRecommendationRequest(RecommendRequest):
    questions: List[str]
    answers: List[str]