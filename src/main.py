from fastapi import FastAPI
from users.router import router as users_router
from tasks.router import router as tasks_router
import models
from database import engine

app = FastAPI()

# include users router
app.include_router(users_router)

# include tasks router
app.include_router(tasks_router)

# Create tables for development (Alembic handles migrations for production)
models.Base.metadata.create_all(bind=engine)


@app.get("/")
async def root():
    return {"message": "Hello World"}