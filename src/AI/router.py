from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from database import get_db
from AI.schema import *
from tasks.schemas import *
from models.task import *
from AI import service

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
@router.post("/regenerate-questions", response_model=QuestionsResponse)
async def regenerate_questions(
    payload: RecommendResponse,
    db: Session = Depends(get_db)
):
    """
    Generate 3 questions to help improve the recommendation.
    Call this when user is unsatisfied with the recommended tasks.
    """
    result = await service.regenerate_questions(db, payload)
    if result is None:
        raise HTTPException(404, "Failed to generate questions")
    return result


@router.post("/regenerate-recommendations", response_model=RecommendResponse)
async def regenerate_recommendations(
    payload: QuestionsResponse,
    db: Session = Depends(get_db)
):
    """
    Regenerate task recommendations based on user feedback.
    Takes the answers to refinement questions and provides improved recommendations.
    """
    # Extract context from payload
    context = RecommendResponse(
        time=payload.time if hasattr(payload, 'time') else 30,
        mode=payload.mode if hasattr(payload, 'mode') else "Focus",
        place=payload.place if hasattr(payload, 'place') else None,
        tool=payload.tool if hasattr(payload, 'tool') else []
    )
    
    result = await service.regenerate_recommendations(db, context, payload)
    if result is None:
        raise HTTPException(404, "Failed to regenerate recommendations")
    return result
