from pydantic import BaseModel

class ClassCreate(BaseModel):
    class_id: str
    class_name: str
    subject_name: str
    lecturer_name: str

class ClassResponse(ClassCreate):
    class Config:
        from_attributes = True
