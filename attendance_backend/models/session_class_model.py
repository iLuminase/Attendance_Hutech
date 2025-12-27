from sqlalchemy import Column, ForeignKey, Integer, String

from app.database import Base


class SessionClass(Base):
    __tablename__ = "session_classes"

    session_id = Column(
        Integer, ForeignKey("sessions.session_id", ondelete="CASCADE"), primary_key=True
    )
    class_id = Column(
        String(20), ForeignKey("classes.class_id", ondelete="CASCADE"), primary_key=True
    )
