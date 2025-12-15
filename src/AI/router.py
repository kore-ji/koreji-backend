from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from database import get_db
from AI.schema import *
from tasks.schemas import *
from models.task import *

router = APIRouter(prefix="/api/recommend", tags=["recommendations"])

# ----- AI Recommend Tasks -----
@router.post("/", response_model=List[TaskResponse])
def recommend_tasks(
    payload: RecommendRequest,
    db: Session = Depends(get_db)
):
   # Todo
   return

# ----- AI Regenerate Recommendation -----
@router.post("/regenerate-questions", response_model=RecommendationQuestionsResponse)
async def regenerate_questions(payload: RecommendationQuestionsRequest, db: Session = Depends(get_db)):
    """
    Generate 3 questions to help improve the recommendation.
    """
    # Todo
    return


@router.post("/regenerate-recommendation", response_model=TaskResponse)
async def regenerate_subtasks(payload: RegenerateRecommendationRequest, db: Session = Depends(get_db)):
    # Todo
    return
