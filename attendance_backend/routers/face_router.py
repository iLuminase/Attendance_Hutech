# routers/face_router.py
from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from typing import List, Dict, Any
import cv2
import numpy as np
import io
import json

from services.database_service import db_service
from models.student import Student
from services.face_service import face_service, extract_face_encoding

router = APIRouter(prefix="/api/face", tags=["face-recognition"])

@router.post("/detect", response_model=Dict[str, Any])
async def detect_faces_endpoint(file: UploadFile = File(...)):
    """API phát hiện khuôn mặt trong ảnh"""
    try:
        # Read image
        image_bytes = await file.read()
        
        # Preprocess image
        img = face_service.preprocess_image(image_bytes)
        if img is None:
            raise HTTPException(status_code=400, detail="Invalid image format")
        
        # Detect faces
        faces = face_service.detect_faces(img)
        
        return {
            "success": True,
            "faces_count": len(faces),
            "faces": faces,
            "message": f"Detected {len(faces)} face(s)"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing image: {str(e)}")

@router.post("/recognize")
async def recognize_faces_endpoint(
    file: UploadFile = File(...),
    db: Session = Depends(db_service.get_db)
):
    """API nhận diện khuôn mặt và trả về thông tin sinh viên"""
    try:
        # Read image
        image_bytes = await file.read()
        
        # Preprocess image
        img = face_service.preprocess_image(image_bytes)
        if img is None:
            raise HTTPException(status_code=400, detail="Invalid image format")
        
        # Detect faces
        faces = face_service.detect_faces(img)
        
        if not faces:
            return {
                "success": True,
                "faces_count": 0,
                "faces": [],
                "recognized_students": [],
                "message": "No faces detected"
            }
        
        # Get all students with face encodings
        students = db.query(Student).filter(Student.face_encoding.isnot(None)).all()
        
        recognized_students = []
        
        # Process each detected face
        for face in faces:
            face_encoding = face_service.extract_face_encoding(img, face)
            
            if face_encoding is None:
                recognized_students.append(None)
                continue
            
            best_match = None
            best_similarity = 0.0
            
            # Compare with all known students
            for student in students:
                student_encoding = student.get_face_encoding()
                if student_encoding is None:
                    continue
                
                is_match, similarity = face_service.compare_faces(
                    face_encoding, student_encoding, threshold=0.7
                )
                
                if is_match and similarity > best_similarity:
                    best_similarity = similarity
                    best_match = student
            
            if best_match:
                recognized_students.append({
                    'student_id': best_match.student_id,
                    'name': best_match.name,
                    'email': best_match.email,
                    'class_id': best_match.class_id,
                    'similarity': best_similarity,
                    'face_box': face
                })
            else:
                recognized_students.append(None)
        
        # Create annotated image
        annotated_img = face_service.draw_face_boxes(img, faces, recognized_students)
        
        # Convert image to bytes for response
        _, buffer = cv2.imencode('.jpg', annotated_img)
        annotated_bytes = buffer.tobytes()
        
        return {
            "success": True,
            "faces_count": len(faces),
            "faces": faces,
            "recognized_count": sum(1 for s in recognized_students if s is not None),
            "recognized_students": recognized_students,
            "message": f"Recognized {sum(1 for s in recognized_students if s is not None)} out of {len(faces)} faces"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error recognizing faces: {str(e)}")

@router.post("/recognize-with-image")
async def recognize_faces_with_image_endpoint(
    file: UploadFile = File(...),
    db: Session = Depends(db_service.get_db)
):
    """API nhận diện khuôn mặt và trả về ảnh có khoanh vùng + thông tin"""
    try:
        # Read image
        image_bytes = await file.read()
        
        # Preprocess image
        img = face_service.preprocess_image(image_bytes)
        if img is None:
            raise HTTPException(status_code=400, detail="Invalid image format")
        
        # Detect faces
        faces = face_service.detect_faces(img)
        
        if not faces:
            # Return original image if no faces
            _, buffer = cv2.imencode('.jpg', img)
            return StreamingResponse(
                io.BytesIO(buffer.tobytes()),
                media_type="image/jpeg",
                headers={"X-Faces-Count": "0", "X-Recognized-Count": "0"}
            )
        
        # Get all students with face encodings
        students = db.query(Student).filter(Student.face_encoding.isnot(None)).all()
        
        recognized_students = []
        
        # Process each detected face
        for face in faces:
            face_encoding = face_service.extract_face_encoding(img, face)
            
            if face_encoding is None:
                recognized_students.append(None)
                continue
            
            best_match = None
            best_similarity = 0.0
            
            # Compare with all known students
            for student in students:
                student_encoding = student.get_face_encoding()
                if student_encoding is None:
                    continue
                
                is_match, similarity = face_service.compare_faces(
                    face_encoding, student_encoding, threshold=0.7
                )
                
                if is_match and similarity > best_similarity:
                    best_similarity = similarity
                    best_match = student
            
            if best_match:
                recognized_students.append({
                    'student_id': best_match.student_id,
                    'name': best_match.name,
                    'similarity': best_similarity
                })
            else:
                recognized_students.append(None)
        
        # Create annotated image
        annotated_img = face_service.draw_face_boxes(img, faces, recognized_students)
        
        # Convert to bytes
        _, buffer = cv2.imencode('.jpg', annotated_img)
        
        recognized_count = sum(1 for s in recognized_students if s is not None)
        
        return StreamingResponse(
            io.BytesIO(buffer.tobytes()),
            media_type="image/jpeg",
            headers={
                "X-Faces-Count": str(len(faces)),
                "X-Recognized-Count": str(recognized_count),
                "X-Recognition-Data": json.dumps(recognized_students)
            }
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing image: {str(e)}")

@router.post("/enroll/{student_id}")
async def enroll_student_face(
    student_id: str,
    file: UploadFile = File(...),
    db: Session = Depends(db_service.get_db)
):
    """API đăng ký khuôn mặt cho sinh viên"""
    try:
        # Find student
        student = db.query(Student).filter(Student.student_id == student_id).first()
        if not student:
            raise HTTPException(status_code=404, detail="Student not found")
        
        # Read image
        image_bytes = await file.read()
        
        # Extract face encoding
        face_encoding = extract_face_encoding(image_bytes)
        if face_encoding is None:
            raise HTTPException(status_code=400, detail="No face detected in image")
        
        # Save encoding
        student.set_face_encoding(face_encoding)
        db.commit()
        
        return {
            "success": True,
            "message": f"Face enrolled successfully for student {student_id}",
            "student": student.to_dict()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error enrolling face: {str(e)}")

@router.delete("/enroll/{student_id}")
async def remove_student_face(
    student_id: str,
    db: Session = Depends(db_service.get_db)
):
    """API xóa khuôn mặt đã đăng ký của sinh viên"""
    try:
        student = db.query(Student).filter(Student.student_id == student_id).first()
        if not student:
            raise HTTPException(status_code=404, detail="Student not found")
        
        student.face_encoding = None
        db.commit()
        
        return {
            "success": True,
            "message": f"Face encoding removed for student {student_id}"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error removing face: {str(e)}")