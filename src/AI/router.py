from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from database import get_db
from .schemas import *
from tasks.schemas import *
from models.task import *
from AI import service

# Prefer importing the helper that calls LLM and returns parsed JSON
try:
    from .testllm import get_recommendation_from_db_and_llm
except Exception:
    # fallback if module layout differs
    try:
        from src.AI.testllm import get_recommendation_from_db_and_llm
    except Exception:
        get_recommendation_from_db_and_llm = None

# Try common DB dependency import locations
try:
    from database import get_db
except Exception:
    try:
        from src.database import get_db
    except Exception:
        get_db = None


router = APIRouter(prefix="/api/recommend", tags=["recommend"])

# ----- AI Recommend Tasks -----
@router.post("/", response_model=RecommendResponse)
def recommend(req: RecommendRequest, db=Depends(get_db) if get_db else None):
    # map frontend payload -> recommender input
    tools = [t.strip() for t in req.tool.split(",") if t.strip()] if req.tool else []
    user_current = {
        "available_minutes": req.time,
        "current_place": req.place,
        "mode": req.mode,
        "tools": tools,
    }

    if get_recommendation_from_db_and_llm is None:
        raise HTTPException(status_code=500, detail="LLM helper not available")

    if db is None:
        raise HTTPException(status_code=500, detail="DB dependency not configured")

    try:
        data = get_recommendation_from_db_and_llm(db, user_current)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    # Expecting `data` to be the parsed JSON that testllm returned
    # If it already contains `recommended_tasks`, return it directly; otherwise try to adapt.
    if isinstance(data, dict) and "recommended_tasks" in data:
        return RecommendResponse(
            time=req.time, 
            mode=req.mode, 
            place=req.place, 
            tool=req.tool, 
            recommended_tasks=data["recommended_tasks"]
        )

    # Fallback: return empty structure if unexpected shape
    return RecommendResponse(
        time=req.time,
        mode=req.mode,
        place=req.place,
        tool=req.tool,
        recommended_tasks=[]
    )

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