from pydantic import BaseModel, EmailStr

class UserBase(BaseModel):
    name: str
    email: EmailStr

class UserCreate(UserBase):
    pass

class UserResponse(UserBase):
    id: str

    class Config:
        orm_mode = True