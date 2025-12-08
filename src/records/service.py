from datetime import datetime
import uuid
from .schema import *
from models.record import Record
from sqlalchemy.orm import Session
from typing import List

class RecordService:
    @ staticmethod
    def get_records(db: Session) -> List[Record]:
        return db.query(Record).all()
    
    @ staticmethod
    def create_record(db: Session, record_data: RecordCreate) -> Record:
        new_record = Record(
            id=uuid.uuid4(),
            task_id=record_data.task_id,
            user_id=record_data.user_id,
            mode=record_data.mode,
            place=record_data.place,
            tool=record_data.tool,
            occurred_at=record_data.occurred_at,
            event_type=EventType.INPROGRESS
        )
        db.add(new_record)
        db.commit()
        db.refresh(new_record)
        return new_record
    
    @ staticmethod
    def update_record(db: Session, record_id: uuid.UUID, new_record: RecordUpdate) -> Record:
        record = db.query(Record).filter(Record.id == record_id).first()
        if record:
            record.event_type = new_record.event_type
            record.updated_at = new_record.updated_at
            if new_record.event_type == EventType.COMPLETE or new_record.event_type == EventType.QUIT:
                record.duration_seconds = (new_record.updated_at - record.occurred_at).seconds

            db.commit()
            db.refresh(record)
        return record
    