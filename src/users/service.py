from sqlalchemy.orm import Session
from typing import List
from models import User
import uuid
from models.user import UserContext, ModeEnum, ToolEnum

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

class ContextService:
    
    @staticmethod
    def parse_tool_string(tool_str: str):
        """
        "phone, laptop" → ["phone", "laptop"]
        """
        return [t.strip() for t in tool_str.split(",")]
    
    @staticmethod
    def create_context(db: Session, data):
        tool_list = ContextService.parse_tool_string(data.tool)

        # 轉成 Enum（不會報錯，因為 enum value 與字串一致）
        tool_enum_list = [ToolEnum(t) for t in tool_list]

        db_obj = UserContext(
            time=data.time,
            mode=ModeEnum(data.mode),  
            place=data.place,
            tool=tool_enum_list
        )
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    @staticmethod
    def get_contexts(db:Session):
        return db.query(UserContext).all()
    
    @staticmethod
    def get_metadata(db: Session):
        return {
            "mode": [m.value for m in ModeEnum],
            "tool": [t.value for t in ToolEnum],
        }
