import json
import os
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.AI.recommend import TaskRecommender


def main():
    # 讀取 .env
    load_dotenv()

    DATABASE_URL = os.getenv("DATABASE_URL")
    if not DATABASE_URL:
        raise RuntimeError("DATABASE_URL not found in .env")

    # 建立 DB session
    engine = create_engine(DATABASE_URL)
    SessionLocal = sessionmaker(bind=engine)
    db = SessionLocal()

    # mock user context（你現在只想測推薦效果，這樣就夠）
    user_context = {
        "available_minutes": 30,
        "current_place": "home",
        "mode": "focus",
        "tools": ["computer"],
        "base_profile": {}
    }

    recommender = TaskRecommender(db)

    print("=== START RECOMMENDATION ===")

    result = recommender.rank(user_context)

    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
