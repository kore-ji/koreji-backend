from datetime import datetime, timezone
import uuid
from .schema import *
from models.record import Record
from sqlalchemy.orm import Session
from typing import List

class RecordService:
    @staticmethod
    def get_records(db: Session, user_id: uuid.UUID = None, mode: str = None, place: str = None, tool: list = None) -> List:
        
        # Query only the specified columns
        results = db.query(Record).filter(user_id==user_id, mode==mode, place==place, tool==tool).all()
        
        
        return results
    
    @staticmethod
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
    
    @staticmethod
    def update_record(db: Session, record_id: uuid.UUID, new_record: RecordUpdate) -> Record:
        record = db.query(Record).filter(Record.id == record_id).first()
        if record:
            record.event_type = new_record.event_type
            record.updated_at = new_record.updated_at
            print("New event type:", new_record.event_type, "Same:", new_record.event_type in (EventType.COMPLETE, EventType.QUIT))
            if new_record.event_type in (EventType.COMPLETE, EventType.QUIT):
                # compute duration in seconds treating datetimes as local wall-clock times
                try:
                    delta = new_record.updated_at - record.occurred_at
                    record.duration_seconds = int(delta.total_seconds())
                except Exception as exc:
                    record.duration_seconds = None
                    print("Failed to compute duration seconds:", exc)

            db.commit()
            db.refresh(record)
            return record
        else:
            return None
        
    