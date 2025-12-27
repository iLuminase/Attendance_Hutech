from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime

class StudentBase(BaseModel):
    student_id: str
    name: str
    email: Optional[str] = None
    phone: Optional[str] = None
    class_id: Optional[str] = None

class StudentCreate(StudentBase):
    pass

class StudentUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    class_id: Optional[str] = None

class StudentResponse(StudentBase):
    has_face_encoding: bool = False
    has_face_image: bool = False
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True