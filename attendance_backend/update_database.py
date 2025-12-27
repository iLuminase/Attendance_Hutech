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
        
        # Kiểm tra / chuẩn hoá kiểu class_id (mã lớp dạng string)
        result = db.execute(text("""
            SELECT DATA_TYPE
            FROM INFORMATION_SCHEMA.COLUMNS
            WHERE TABLE_NAME = 'students'
              AND COLUMN_NAME = 'class_id'
        """))

        row = result.fetchone()
        if row is not None:
            data_type = str(row[0]).lower()
            if data_type != 'varchar':
                print("Converting students.class_id to VARCHAR(20)...")
                db.execute(text("""
                    ALTER TABLE students
                    MODIFY COLUMN class_id VARCHAR(20)
                """))

        # Tạo bảng session_classes để hỗ trợ 1 session nhiều lớp
        # Lưu ý: cần đảm bảo có bảng sessions trước, nếu không FK sẽ lỗi (errno 150).
        print("Ensuring sessions table...")
        db.execute(
            text(
                """
                CREATE TABLE IF NOT EXISTS sessions (
                    session_id INT AUTO_INCREMENT PRIMARY KEY,
                    class_id VARCHAR(20) NULL,
                    session_date DATE NOT NULL,
                    start_time TIME NOT NULL,
                    end_time TIME NOT NULL,
                    INDEX idx_sessions_date (session_date),
                    INDEX idx_sessions_class_id (class_id),
                    CONSTRAINT fk_sessions_class FOREIGN KEY (class_id)
                        REFERENCES classes(class_id) ON DELETE SET NULL
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
                """
            )
        )

        print("Ensuring session_classes table...")
        db.execute(
            text(
                """
                CREATE TABLE IF NOT EXISTS session_classes (
                    session_id INT NOT NULL,
                    class_id VARCHAR(20) NOT NULL,
                    PRIMARY KEY (session_id, class_id),
                    CONSTRAINT fk_sc_session FOREIGN KEY (session_id)
                        REFERENCES sessions(session_id) ON DELETE CASCADE,
                    CONSTRAINT fk_sc_class FOREIGN KEY (class_id)
                        REFERENCES classes(class_id) ON DELETE CASCADE
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
                """
            )
        )

        # Backfill dữ liệu legacy: sessions.class_id -> session_classes
        # (Nếu sessions không tồn tại thì câu lệnh này sẽ fail và sẽ được bắt ở except)
        db.execute(
            text(
                """
                INSERT IGNORE INTO session_classes (session_id, class_id)
                SELECT session_id, class_id
                FROM sessions
                WHERE class_id IS NOT NULL AND TRIM(class_id) <> ''
                """
            )
        )

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