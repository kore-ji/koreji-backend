from pydantic import BaseModel
from typing import List, Optional

class RecommendRequest(BaseModel):
    time: int
    mode: str 
    place: Optional[str] = None
    tool: List[str] = []

# ----- Regenerate recommendation Questions -----
class RecommendationQuestionsRequest(RecommendRequest):
    pass

class RecommendationQuestionsResponse(BaseModel):
    questions: List[str]

class RegenerateRecommendationRequest(BaseModel):
    questions: List[str]
    answers: List[str]