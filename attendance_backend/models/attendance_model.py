from datetime import datetime

from sqlalchemy import Column, Date, DateTime, Enum, Float, ForeignKey, Integer, String, Time

from app.database import Base


class Attendance(Base):
    __tablename__ = "attendance"

    id = Column(Integer, primary_key=True, autoincrement=True)
    student_id = Column(String(20), ForeignKey("students.student_id"), nullable=False)
    class_id = Column(String(20), ForeignKey("classes.class_id"), nullable=False)
    attendance_date = Column(Date, nullable=False)
    attendance_time = Column(Time, nullable=False)
    status = Column(Enum("present", "absent", "late"), default="present")
    recognition_confidence = Column(Float, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
