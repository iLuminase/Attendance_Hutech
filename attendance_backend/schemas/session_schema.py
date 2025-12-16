from pydantic import BaseModel
from datetime import date, time
from typing import Optional

class SessionCreate(BaseModel):
    class_id: str
    session_date: date
    start_time: time
    end_time: time

class SessionResponse(BaseModel):
    session_id: int
    class_id: str
    session_date: date
    start_time: time
    end_time: time
    
    class Config:
        from_attributes = True

class SessionUpdate(BaseModel):
    class_id: Optional[str] = None
    session_date: Optional[date] = None
    start_time: Optional[time] = None
    end_time: Optional[time] = None
