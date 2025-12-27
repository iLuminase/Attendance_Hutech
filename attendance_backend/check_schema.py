#!/usr/bin/env python3
"""
Script để kiểm tra schema của bảng students
"""

import sys
import os
sys.path.append(os.path.dirname(__file__))

from sqlalchemy import text
from app.database import SessionLocal, engine

def check_students_schema():
    """Kiểm tra schema của bảng students"""
    db = SessionLocal()
    try:
        # Kiểm tra tất cả các cột trong bảng students
        check_columns_query = text("""
            SELECT COLUMN_NAME, DATA_TYPE, IS_NULLABLE, COLUMN_DEFAULT
            FROM INFORMATION_SCHEMA.COLUMNS 
            WHERE TABLE_SCHEMA = DATABASE()
            AND TABLE_NAME = 'students'
            ORDER BY ORDINAL_POSITION
        """)

        result = db.execute(check_columns_query).fetchall()

        print("=== SCHEMA CỦA BẢNG STUDENTS ===")
        for row in result:
            column_name, data_type, is_nullable, column_default = row
            print(f"Column: {column_name:<25} Type: {data_type:<15} Nullable: {is_nullable:<5} Default: {column_default}")

        print(f"\nTổng số cột: {len(result)}")

        # Kiểm tra specifically face_image column
        face_image_exists = any(row[0] == 'face_image' for row in result)
        print(f"\nCột face_image có tồn tại: {'✅ Có' if face_image_exists else '❌ Không'}")

        # Kiểm tra dữ liệu mẫu
        print("\n=== KIỂM TRA DỮ LIỆU MẪU ===")
        sample_query = text("""
            SELECT student_id, name, 
                   face_encoding IS NOT NULL as has_face_encoding,
                   face_image IS NOT NULL as has_face_image
            FROM students 
            LIMIT 5
        """)

        sample_result = db.execute(sample_query).fetchall()
        for row in sample_result:
            student_id, name, has_encoding, has_image = row
            print(f"Student: {student_id:<10} Name: {name:<20} Encoding: {'✅' if has_encoding else '❌'} Image: {'✅' if has_image else '❌'}")

    except Exception as e:
        print(f"❌ Lỗi khi kiểm tra schema: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    check_students_schema()
