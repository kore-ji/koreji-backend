from fastapi import FastAPI
from users.router import router as users_router
from tasks.router import router as tasks_router
import models
from database import engine, SessionLocal
from tasks import service as task_service

app = FastAPI()

# include users router
app.include_router(users_router)

# include tasks router
app.include_router(tasks_router)

# Create tables for development (Alembic handles migrations for production)
models.Base.metadata.create_all(bind=engine)

@app.on_event("startup")
def startup_seed_tag_groups():
    db = SessionLocal()
    try:
        task_service.ensure_default_tag_groups(db)
    finally:
        db.close()

@app.get("/")
async def root():
    return {"message": "Hello World"}