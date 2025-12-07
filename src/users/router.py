from fastapi import APIRouter, Depends, status
from .service import UserService,ContextService
from .schema import UserCreate, UserResponse,ContextCreate,ContextResponse
from typing import List
from sqlalchemy.orm import Session
from database import get_db

router = APIRouter(prefix="/api/users", tags=["users"])
context_router = APIRouter(prefix="/api/context", tags=["context"])


@router.get("/", response_model=List[UserResponse])
async def get_users(db: Session = Depends(get_db)):
    users = UserService.get_users(db)
    return users


@router.post("/", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user(user_create: UserCreate, db: Session = Depends(get_db)):
    user = UserService.create_user(db, name=user_create.name, email=user_create.email)
    return user

# Return the dropdown options for mode and tool.
@router.get("/context/metadata")
async def context_metadata(db: Session = Depends(get_db)):
    return ContextService.get_metadata(db)

# @router.get("/context", response_model=List[ContextResponse])
# async def list_contexts(db: Session = Depends(get_db)):
#     return get_contexts(db)


# @router.post("/context", response_model=ContextResponse, status_code=status.HTTP_201_CREATED)
# async def post_context(payload: ContextCreate, db: Session = Depends(get_db)):
#     obj = create_context(db, payload)
#     return obj
