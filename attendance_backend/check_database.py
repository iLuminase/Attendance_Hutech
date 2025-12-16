#!/usr/bin/env python3
"""
Script để kiểm tra và tạo database schema
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import create_engine, text, inspect
from sqlalchemy.exc import SQLAlchemyError
from app.database import DB_URL, Base
from models.student import Student  
from models.class_model import Class
from models.session_model import Session
from models.attendance_model import Attendance
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def check_database_connection():
    """Kiểm tra kết nối database"""
    try:
        engine = create_engine(DB_URL)
        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1"))
            logger.info("✅ Database connection successful")
            return engine
    except Exception as e:
        logger.error(f"❌ Database connection failed: {e}")
        return None

def check_existing_tables(engine):
    """Kiểm tra các bảng hiện có"""
    try:
        inspector = inspect(engine)
        existing_tables = inspector.get_table_names()
        logger.info(f"📋 Existing tables: {existing_tables}")
        
        for table_name in existing_tables:
            columns = inspector.get_columns(table_name)
            logger.info(f"  Table '{table_name}':")
            for col in columns:
                logger.info(f"    - {col['name']}: {col['type']} {'(nullable)' if col['nullable'] else '(not null)'}")
        
        return existing_tables
    except Exception as e:
        logger.error(f"❌ Error checking tables: {e}")
        return []

def create_tables(engine):
    """Tạo các bảng mới"""
    try:
        logger.info("🔨 Creating tables...")
        Base.metadata.create_all(bind=engine)
        logger.info("✅ Tables created successfully")
        return True
    except Exception as e:
        logger.error(f"❌ Error creating tables: {e}")
        return False

def verify_schema(engine):
    """Kiểm tra schema sau khi tạo"""
    try:
        inspector = inspect(engine)
        
        # Kiểm tra bảng students
        if 'students' in inspector.get_table_names():
            columns = [col['name'] for col in inspector.get_columns('students')]
            required_columns = ['id', 'student_id', 'name', 'email', 'phone', 'class_id', 'face_encoding', 'face_encoding_version', 'created_at', 'updated_at']
            
            missing_columns = [col for col in required_columns if col not in columns]
            if missing_columns:
                logger.warning(f"⚠️  Missing columns in 'students' table: {missing_columns}")
                return False
            else:
                logger.info("✅ Students table schema is correct")
        
        # Kiểm tra các bảng khác
        required_tables = ['classes', 'sessions', 'attendance']
        existing_tables = inspector.get_table_names()
        
        for table in required_tables:
            if table in existing_tables:
                logger.info(f"✅ Table '{table}' exists")
            else:
                logger.warning(f"⚠️  Table '{table}' missing")
        
        return True
    except Exception as e:
        logger.error(f"❌ Error verifying schema: {e}")
        return False

def test_student_operations(engine):
    """Test các operations với Student model"""
    try:
        from sqlalchemy.orm import sessionmaker
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        
        db = SessionLocal()
        
        # Test tạo student
        test_student = Student(
            student_id="TEST001",
            name="Test Student",
            email="test@test.com",
            phone="1234567890",
            class_id=1
        )
        
        # Kiểm tra có student nào trùng không
        existing = db.query(Student).filter(Student.student_id == "TEST001").first()
        if existing:
            db.delete(existing)
            db.commit()
        
        db.add(test_student)
        db.commit()
        
        # Test lấy student
        retrieved = db.query(Student).filter(Student.student_id == "TEST001").first()
        if retrieved:
            logger.info("✅ Student operations working")
            logger.info(f"   Retrieved: {retrieved.to_dict()}")
            
            # Test face encoding
            import numpy as np
            test_encoding = np.array([1.0, 2.0, 3.0, 4.0], dtype=np.float32)
            retrieved.set_face_encoding(test_encoding)
            db.commit()
            
            # Verify face encoding
            face_encoding = retrieved.get_face_encoding()
            if face_encoding is not None and len(face_encoding) == 4:
                logger.info("✅ Face encoding operations working")
            else:
                logger.warning("⚠️  Face encoding not working properly")
            
            # Cleanup
            db.delete(retrieved)
            db.commit()
        else:
            logger.error("❌ Could not retrieve student")
            
        db.close()
        return True
        
    except Exception as e:
        logger.error(f"❌ Error testing student operations: {e}")
        return False

def main():
    """Main function"""
    logger.info("🚀 Starting database schema check...")
    
    # 1. Kiểm tra kết nối
    engine = check_database_connection()
    if not engine:
        return
    
    # 2. Kiểm tra bảng hiện có
    existing_tables = check_existing_tables(engine)
    
    # 3. Tạo bảng nếu cần
    if not existing_tables or 'students' not in existing_tables:
        create_tables(engine)
    
    # 4. Kiểm tra schema
    verify_schema(engine)
    
    # 5. Test operations
    test_student_operations(engine)
    
    logger.info("🎉 Database schema check completed!")

if __name__ == "__main__":
    main()