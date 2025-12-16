from sqlalchemy import Column, String, DateTime, LargeBinary
from datetime import datetime
from app.database import Base

class Student(Base):
    __tablename__ = "students"

    student_id = Column(String(20), primary_key=True, index=True)
    full_name = Column(String(100))
    class_id = Column(String(20))
    face_encoding = Column(LargeBinary, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
