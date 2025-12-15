from pydantic import BaseModel
from typing import List

class RecommendRequest(BaseModel):
    time: int
    mode: str
    place: str
    tool: str  # comma-separated values e.g. "phone, computer"

class RecommendedTask(BaseModel):
    task_name: str
    reason: str

class RecommendResponse(BaseModel):
    recommended_tasks: List[RecommendedTask]