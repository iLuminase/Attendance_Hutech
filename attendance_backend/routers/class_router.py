from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from services.database_service import db_service
from models.class_model import Class
from models.class_schema import ClassCreate

router = APIRouter(prefix="/classes", tags=["Classes"])


@router.post("/")
def create_class(data: ClassCreate, db: Session = Depends(db_service.get_db)):
    """Tạo lớp học mới"""
    try:
        # Kiểm tra lớp đã tồn tại chưa
        existing = db.query(Class).filter(Class.class_id == data.class_id).first()
        if existing:
            raise HTTPException(status_code=400, detail="Lớp học đã tồn tại")

        new_class = Class(**data.model_dump())
        db.add(new_class)
        db.commit()
        db.refresh(new_class)

        return {
            "message": "Tạo lớp học thành công",
            "class_id": new_class.class_id
        }
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Lỗi tạo lớp học: {str(e)}")

@router.get("/")
def get_classes(db: Session = Depends(db_service.get_db)):
    """Lấy danh sách tất cả lớp học"""
    try:
        classes = db.query(Class).all()
        return {
            "total": len(classes),
            "classes": classes
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Lỗi lấy danh sách lớp: {str(e)}")

@router.get("/{class_id}")
def get_class(class_id: str, db: Session = Depends(db_service.get_db)):
    """Lấy thông tin lớp học theo ID"""
    class_obj = db.query(Class).filter(Class.class_id == class_id).first()
    if not class_obj:
        raise HTTPException(status_code=404, detail="Không tìm thấy lớp học")
    return class_obj
