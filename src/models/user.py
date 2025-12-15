import uuid
from sqlalchemy import Column, String, DateTime,Integer,Text,Enum
from sqlalchemy.dialects.postgresql import UUID,ARRAY
from datetime import datetime
from database import Base
import enum

# Define mode using Enum
class ModeEnum(str,enum.Enum):
    noSelect = "noSelect"
    relax = "relax"
    focus = "focus"
    exercise = "exercise"
    social = "social"

# Define tool using Enum
class ToolEnum(str,enum.Enum):
    noSelect = "noSelect"
    Phone = "phone"
    computer = "computer"
    ipad = "ipad"
    textbook = "textbook"
    notebook = "notebook"

# context table 
class UserContext(Base):
    __tablename__ = "user_context"

    id = Column(Integer, primary_key=True, index=True)
    time = Column(Integer, nullable=False)
    mode = Column(Enum(ModeEnum), nullable=False)
    place = Column(Text, nullable=False)
    tool = Column(ARRAY(Enum(ToolEnum)), nullable=False)

    # timestamps
    created_at = Column(Text, server_default="NOW()")
    updated_at = Column(Text, server_default="NOW()")


class User(Base):
    __tablename__ = 'users'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, unique=True, nullable=False)
    name = Column(String(255), nullable=False)
    email = Column(String(255), unique=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)