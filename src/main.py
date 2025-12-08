import os
from fastapi import FastAPI
from records.router import router as records_router
from fastapi.middleware.cors import CORSMiddleware
from users.router import router as users_router
from tasks.router import router as tasks_router
import models

from database import engine
from dotenv import load_dotenv

app = FastAPI()

# Load environment from .env before reading settings
load_dotenv()

# CORS for frontend dev — parse comma-separated origins
allow_origins_env = os.getenv("ALLOW_ORIGINS", "")
allow_origins = [
    origin.strip()
    for origin in allow_origins_env.split(",")
    if origin.strip()
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allow_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# include users router
app.include_router(users_router)
app.include_router(records_router)

# include tasks router
app.include_router(tasks_router)

# Create tables for development (Alembic handles migrations for production)
models.Base.metadata.create_all(bind=engine)


@app.get("/")
async def root():
    return {"message": "Hello World"}