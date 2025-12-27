# models/student.py
from sqlalchemy import Column, DateTime, ForeignKey, LargeBinary, String
from sqlalchemy.orm import relationship
from app.database import Base
from datetime import datetime
import json
import numpy as np

class Student(Base):
    __tablename__ = "students"

    student_id = Column(String(20), primary_key=True, index=True, nullable=False)
    name = Column(String(100), nullable=False)
    email = Column(String(100), unique=True, index=True)
    phone = Column(String(15))
    class_id = Column(String(20), ForeignKey("classes.class_id"), index=True)
    face_encoding = Column(LargeBinary)  # Store face encoding as binary
    face_image = Column(LargeBinary)  # Store face image as binary
    face_encoding_version = Column(String(10), default="1.0")  # For future compatibility
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    # Relationship
    class_info = relationship("Class")
    
    def set_face_encoding(self, encoding: np.ndarray):
        """Lưu face encoding"""
        if encoding is not None:
            self.face_encoding = encoding.tobytes()
    
    def get_face_encoding(self) -> np.ndarray:
        """Lấy face encoding"""
        if self.face_encoding:
            return np.frombuffer(self.face_encoding, dtype=np.float32)
        return None
    
    def set_face_image(self, image_bytes: bytes):
        """Lưu face image"""
        if image_bytes is not None:
            self.face_image = image_bytes

    def get_face_image(self) -> bytes:
        """Lấy face image"""
        return self.face_image

    def to_dict(self):
        return {
            'student_id': self.student_id,
            'name': self.name,
            'email': self.email,
            'phone': self.phone,
            'class_id': self.class_id,
            'has_face_encoding': self.face_encoding is not None,
            'has_face_image': self.face_image is not None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }