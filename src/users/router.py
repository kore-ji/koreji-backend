from fastapi import APIRouter, Depends, status
from .service import UserService
from .schema import UserCreate, UserResponse
from typing import List
from sqlalchemy.orm import Session
from database import get_db

router = APIRouter(prefix="/api/users", tags=["users"])


@router.get("/", response_model=List[UserResponse])
async def get_users(db: Session = Depends(get_db)):
    users = UserService.get_users(db)
    return users


@router.post("/", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user(user_create: UserCreate, db: Session = Depends(get_db)):
    user = UserService.create_user(db, name=user_create.name, email=user_create.email)
    return user