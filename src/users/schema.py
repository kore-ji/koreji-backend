from pydantic import BaseModel, EmailStr,ConfigDict
from typing import List, Optional
from uuid import UUID

class UserBase(BaseModel):
    name: str
    email: EmailStr

class UserCreate(UserBase):
    pass

class UserResponse(UserBase):
    id: UUID

    # class Config:
    #     orm_mode = True
    model_config = ConfigDict(from_attributes=True)

# Schema for home page
class ContextCreate(BaseModel):
    time: int
    mode: str
    place: str
    tool: str 

class ContextResponse(BaseModel):
    id : int
    time : int
    mode : str
    place : str
    tool : List[str]
    created_at : Optional[str] = None
    updated_at : Optional[str] = None

    model_config = ConfigDict(from_attributes=True)