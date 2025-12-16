from sqlalchemy import Column, Integer, String, DateTime, Enum
from datetime import datetime
from app.database import Base

class Attendance(Base):
    __tablename__ = "attendance"

    attendance_id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(Integer)
    student_id = Column(String(20))
    checkin_time = Column(DateTime, default=datetime.utcnow)
    status = Column(Enum("ON_TIME", "LATE", "ABSENT"))
