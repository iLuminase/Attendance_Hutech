from pydantic import BaseModel
from datetime import date, time
from typing import List, Optional

class SessionCreate(BaseModel):
    # Hỗ trợ legacy: tạo session 1 lớp
    class_id: Optional[str] = None
    # Hỗ trợ mới: 1 session nhiều lớp
    class_ids: Optional[List[str]] = None
    session_date: date
    start_time: time
    end_time: time

class SessionResponse(BaseModel):
    session_id: int
    class_id: Optional[str] = None
    class_ids: Optional[List[str]] = None
    session_date: date
    start_time: time
    end_time: time
    
    class Config:
        from_attributes = True

class SessionUpdate(BaseModel):
    class_id: Optional[str] = None
    class_ids: Optional[List[str]] = None
    session_date: Optional[date] = None
    start_time: Optional[time] = None
    end_time: Optional[time] = None
