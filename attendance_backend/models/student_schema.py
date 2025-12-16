from pydantic import BaseModel

class StudentCreate(BaseModel):
    student_id: str
    full_name: str
    class_id: str

class StudentResponse(StudentCreate):
    class Config:
        from_attributes = True
