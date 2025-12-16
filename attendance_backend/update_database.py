#!/usr/bin/env python3
"""
Script để cập nhật database schema cho face recognition
"""

from sqlalchemy import text
from services.database_service import db_service

def update_database_schema():
    """Cập nhật database schema để thêm face encoding columns"""
    
    try:
        # Kết nối database
        db = next(db_service.get_db())
        
        # Kiểm tra xem cột face_encoding đã tồn tại chưa
        result = db.execute(text("""
            SELECT COLUMN_NAME 
            FROM INFORMATION_SCHEMA.COLUMNS 
            WHERE TABLE_NAME = 'students' 
            AND COLUMN_NAME = 'face_encoding'
        """))
        
        if result.fetchone() is None:
            print("Adding face_encoding column...")
            db.execute(text("""
                ALTER TABLE students 
                ADD COLUMN face_encoding LONGBLOB
            """))
            
        # Kiểm tra cột face_encoding_version
        result = db.execute(text("""
            SELECT COLUMN_NAME 
            FROM INFORMATION_SCHEMA.COLUMNS 
            WHERE TABLE_NAME = 'students' 
            AND COLUMN_NAME = 'face_encoding_version'
        """))
        
        if result.fetchone() is None:
            print("Adding face_encoding_version column...")
            db.execute(text("""
                ALTER TABLE students 
                ADD COLUMN face_encoding_version VARCHAR(10) DEFAULT '1.0'
            """))
        
        db.commit()
        print("✅ Database schema updated successfully!")
        
    except Exception as e:
        print(f"❌ Error updating database: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    update_database_schema()