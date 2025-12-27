#!/usr/bin/env python3
"""
Script để thêm cột face_image vào bảng students
"""

import sys
import os
sys.path.append(os.path.dirname(__file__))

from sqlalchemy import text
from app.database import SessionLocal, engine

def add_face_image_column():
    """Thêm cột face_image vào bảng students"""
    db = SessionLocal()
    try:
        # Kiểm tra xem cột face_image đã tồn tại chưa
        check_column_query = text("""
            SELECT COUNT(*) 
            FROM INFORMATION_SCHEMA.COLUMNS 
            WHERE TABLE_SCHEMA = DATABASE()
            AND TABLE_NAME = 'students' 
            AND COLUMN_NAME = 'face_image'
        """)

        result = db.execute(check_column_query).fetchone()
        if result[0] == 0:
            print("Adding face_image column...")
            # Thêm cột face_image
            add_column_query = text("""
                ALTER TABLE students 
                ADD COLUMN face_image LONGBLOB
            """)
            db.execute(add_column_query)
            db.commit()
            print("✅ Đã thêm cột face_image vào bảng students!")
        else:
            print("✅ Cột face_image đã tồn tại trong bảng students!")

    except Exception as e:
        print(f"❌ Lỗi khi thêm cột face_image: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    add_face_image_column()
