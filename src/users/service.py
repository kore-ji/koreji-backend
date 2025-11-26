from sqlalchemy.orm import Session
from typing import List
from models import User
import uuid

class UserService:
    
    @staticmethod
    def get_users(db: Session) -> List[User]:
        return db.query(User).all()
    
    @staticmethod
    def create_user(db: Session, name: str, email: str) -> User:
        new_user = User(id=uuid.uuid4(), name=name, email=email)
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        return new_user