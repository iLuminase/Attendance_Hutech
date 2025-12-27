from datetime import date, datetime, time
from typing import List, Optional

from pydantic import BaseModel


class AttendanceRecordResponse(BaseModel):
    attendance_id: Optional[int] = None
    student_id: str
    student_name: Optional[str] = None
    student_email: Optional[str] = None
    class_id: Optional[str] = None
    class_name: Optional[str] = None
    subject_name: Optional[str] = None
    session_id: Optional[int] = None

    session_date: Optional[date] = None
    start_time: Optional[time] = None
    end_time: Optional[time] = None

    checkin_time: Optional[datetime] = None
    attendance_date: Optional[date] = None
    attendance_time: Optional[time] = None

    status: Optional[str] = None
    recognition_confidence: Optional[float] = None


class AttendanceCheckinByFaceResponse(BaseModel):
    success: bool
    faces_count: int
    recognized_count: int
    attendances_created: int
    attendances: List[AttendanceRecordResponse]
    message: str
