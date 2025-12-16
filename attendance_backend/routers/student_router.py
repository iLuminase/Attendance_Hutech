from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from services.database_service import db_service
from models.student import Student
from models.student_schema import StudentCreate
from typing import List

router = APIRouter(prefix="/students", tags=["Students"])


@router.post("/")
def create_student(student: StudentCreate, db: Session = Depends(db_service.get_db)):
    """Tạo sinh viên mới"""
    try:
        # Kiểm tra sinh viên đã tồn tại chưa
        existing = db.query(Student).filter(Student.student_id == student.student_id).first()
        if existing:
            raise HTTPException(status_code=400, detail="Sinh viên đã tồn tại")

        new_student = Student(**student.model_dump())
        db.add(new_student)
        db.commit()
        db.refresh(new_student)

        return {
            "message": "Tạo sinh viên thành công",
            "student_id": new_student.student_id
        }
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Lỗi tạo sinh viên: {str(e)}")

@router.get("/")
def get_students(db: Session = Depends(db_service.get_db)):
    """Lấy danh sách tất cả sinh viên"""
    try:
        students = db.query(Student).all()
        return {
            "total": len(students),
            "students": students
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Lỗi lấy danh sách sinh viên: {str(e)}")

@router.get("/{student_id}")
def get_student(student_id: str, db: Session = Depends(db_service.get_db)):
    """Lấy thông tin sinh viên theo ID"""
    student = db.query(Student).filter(Student.student_id == student_id).first()
    if not student:
        raise HTTPException(status_code=404, detail="Không tìm thấy sinh viên")
    return student

@router.delete("/{student_id}")
def delete_student(student_id: str, db: Session = Depends(db_service.get_db)):
    """Xóa sinh viên theo ID"""
    try:
        student = db.query(Student).filter(Student.student_id == student_id).first()
        if not student:
            raise HTTPException(status_code=404, detail="Không tìm thấy sinh viên")

        db.delete(student)
        db.commit()
        return {"message": f"Đã xóa sinh viên {student_id}"}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Lỗi xóa sinh viên: {str(e)}")
