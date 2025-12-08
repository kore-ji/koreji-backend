import uuid
import schema
from models.record import Record
from sqlalchemy.orm import Session
from typing import List

class RecordService:
    @ staticmethod
    def get_records(db: Session) -> List[Record]:
        return db.query(Record).all()
    
    @ staticmethod
    def create_record(db: Session, record_data: schema.RecordCreate) -> Record:
        new_record = Record(
            id=uuid.uuid4(),
            task_id=record_data.task_id,
            user_id=record_data.user_id,
            mode=record_data.mode,
            place=record_data.place,
            tool=record_data.tool,
            duration_seconds=0, 
            
        )
        db.add(new_record)
        db.commit()
        db.refresh(new_record)
        return new_record