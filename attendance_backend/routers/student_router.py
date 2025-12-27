from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from fastapi.responses import Response
from sqlalchemy.orm import Session
from services.database_service import db_service
from services.face_service import extract_face_encoding
from models.student import Student
from schemas.student_schema import StudentCreate, StudentResponse, StudentUpdate
from typing import List
router = APIRouter(prefix="/students", tags=["Students"])


@router.post("/", response_model=StudentResponse)
def create_student(student: StudentCreate, db: Session = Depends(db_service.get_db)):
    """Tạo sinh viên mới"""
    try:
        # Kiểm tra sinh viên đã tồn tại chưa
        existing = db.query(Student).filter(Student.student_id == student.student_id).first()
        if existing:
            raise HTTPException(status_code=400, detail="Student already exists")

        new_student = Student(**student.model_dump())
        db.add(new_student)
        db.commit()
        db.refresh(new_student)

        return new_student
    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error creating student: {str(e)}")

@router.get("/", response_model=List[StudentResponse])
def get_students(db: Session = Depends(db_service.get_db)):
    """Lấy danh sách tất cả sinh viên"""
    try:
        students = db.query(Student).all()
        return students
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting students: {str(e)}")

@router.get("/{student_id}", response_model=StudentResponse)
def get_student(student_id: str, db: Session = Depends(db_service.get_db)):
    """Lấy thông tin sinh viên theo ID"""
    student = db.query(Student).filter(Student.student_id == student_id).first()
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")
    return student

@router.put("/{student_id}", response_model=StudentResponse)
def update_student(student_id: str, student_data: StudentUpdate, db: Session = Depends(db_service.get_db)):
    """Cập nhật thông tin sinh viên"""
    try:
        # Tìm sinh viên
        student = db.query(Student).filter(Student.student_id == student_id).first()
        if not student:
            raise HTTPException(status_code=404, detail="Student not found")

        # Cập nhật các trường được cung cấp
        update_data = student_data.model_dump(exclude_unset=True)

        for field, value in update_data.items():
            if hasattr(student, field):
                setattr(student, field, value)

        # Cập nhật updated_at
        from datetime import datetime
        student.updated_at = datetime.now()

        db.commit()
        db.refresh(student)

        return student

    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error updating student: {str(e)}")

@router.delete("/{student_id}")
def delete_student(student_id: str, db: Session = Depends(db_service.get_db)):
    """Xóa sinh viên theo ID"""
    try:
        student = db.query(Student).filter(Student.student_id == student_id).first()
        if not student:
            raise HTTPException(status_code=404, detail="Student not found")

        db.delete(student)
        db.commit()
        return {"message": f"Student {student_id} deleted successfully"}
    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error deleting student: {str(e)}")


@router.post("/{student_id}/upload-face")
async def upload_face(
    student_id: str,
    file: UploadFile = File(...),
    db: Session = Depends(db_service.get_db)
):
    """Upload face image for student and extract face encoding"""
    try:
        # Kiểm tra student tồn tại
        student = db.query(Student).filter(Student.student_id == student_id).first()
        if not student:
            raise HTTPException(status_code=404, detail="Student not found")

        # Đọc file ảnh
        image_bytes = await file.read()
        
        # Validate file type
        if not file.content_type or not file.content_type.startswith('image/'):
            raise HTTPException(status_code=400, detail="File must be an image")

        # Trích xuất face encoding
        encoding = extract_face_encoding(image_bytes)
        if encoding is None:
            raise HTTPException(status_code=400, detail="No face detected in image. Please upload a clear photo with a visible face.")

        # Lưu encoding và face image sử dụng method từ model
        student.set_face_encoding(encoding)
        student.set_face_image(image_bytes)
        db.commit()

        return {
            "message": "Face encoding saved successfully",
            "student_id": student_id,
            "encoding_size": len(encoding) if encoding is not None else 0
        }
        
    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error processing image: {str(e)}")

@router.get("/{student_id}/face-image")
def get_student_face_image(student_id: str, db: Session = Depends(db_service.get_db)):
    """Lấy ảnh khuôn mặt của sinh viên"""
    try:
        # Tìm sinh viên
        student = db.query(Student).filter(Student.student_id == student_id).first()
        if not student:
            raise HTTPException(status_code=404, detail="Student not found")

        # Kiểm tra có ảnh không
        if not student.face_image:
            raise HTTPException(status_code=404, detail="No face image found for this student")

        # Trả về ảnh
        return Response(
            content=student.get_face_image(),
            media_type="image/jpeg",
            headers={
                "Content-Disposition": f"inline; filename=student_{student_id}_face.jpg",
                "Cache-Control": "public, max-age=3600"  # Cache 1 hour
            }
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving image: {str(e)}")

@router.get("/{student_id}/has-face-image")
def check_student_has_face_image(student_id: str, db: Session = Depends(db_service.get_db)):
    """Kiểm tra sinh viên có ảnh khuôn mặt không"""
    try:
        # Tìm sinh viên
        student = db.query(Student).filter(Student.student_id == student_id).first()
        if not student:
            raise HTTPException(status_code=404, detail="Student not found")

        return {
            "student_id": student_id,
            "has_face_image": student.face_image is not None,
            "has_face_encoding": student.face_encoding is not None
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error checking face image: {str(e)}")

@router.get("/{student_id}/face-thumbnail")
def get_student_face_thumbnail(student_id: str, size: int = 150, db: Session = Depends(db_service.get_db)):
    """Lấy thumbnail ảnh khuôn mặt của sinh viên"""
    try:
        from services.face_service import create_face_thumbnail

        # Tìm sinh viên
        student = db.query(Student).filter(Student.student_id == student_id).first()
        if not student:
            raise HTTPException(status_code=404, detail="Student not found")

        # Kiểm tra có ảnh không
        if not student.face_image:
            raise HTTPException(status_code=404, detail="No face image found for this student")

        # Tạo thumbnail
        thumbnail_bytes = create_face_thumbnail(student.get_face_image(), (size, size))
        if not thumbnail_bytes:
            raise HTTPException(status_code=500, detail="Failed to create thumbnail")

        # Trả về thumbnail
        return Response(
            content=thumbnail_bytes,
            media_type="image/jpeg",
            headers={
                "Content-Disposition": f"inline; filename=student_{student_id}_thumbnail.jpg",
                "Cache-Control": "public, max-age=3600"  # Cache 1 hour
            }
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating thumbnail: {str(e)}")
