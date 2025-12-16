from sqlalchemy import Column, Integer, String, Date, Time, ForeignKey
from sqlalchemy.orm import relationship
from app.database import Base

class Session(Base):
    __tablename__ = "sessions"

    session_id = Column(Integer, primary_key=True, autoincrement=True)
    class_id = Column(String(20), ForeignKey("classes.class_id"))
    session_date = Column(Date)
    start_time = Column(Time)
    end_time = Column(Time)
    
    # Relationship
    class_info = relationship("Class", back_populates="sessions")
