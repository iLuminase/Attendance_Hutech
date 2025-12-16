from sqlalchemy import Column, String
from sqlalchemy.orm import relationship
from app.database import Base

class Class(Base):
    __tablename__ = "classes"

    class_id = Column(String(20), primary_key=True)
    class_name = Column(String(100))
    subject_name = Column(String(100))
    lecturer_name = Column(String(100))
    
    # Relationship
    sessions = relationship("Session", back_populates="class_info")
