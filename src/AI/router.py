from fastapi import APIRouter, Depends, HTTPException
from typing import List
from .schemas import RecommendRequest, RecommendResponse, RecommendedTask

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

router = APIRouter(prefix="/api")

@router.post("/recommend", response_model=RecommendResponse)
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
        return data

    # Fallback: return empty structure if unexpected shape
    return {"recommended_tasks": []}