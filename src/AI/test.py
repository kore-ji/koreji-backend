from AI.context import build_user_context
from AI.recommend import TaskRecommender

raw_input = {
    "available_minutes": 30,
    "mode": "focus",
    "tool": "computer",
    "place": "home"
}

user_context = build_user_context(raw_input, user_profile={})

engine = TaskRecommender()
result = engine.rank(user_context)