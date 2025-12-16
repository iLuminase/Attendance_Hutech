"""
Script tạo database và tables cho MySQL
Run this script để tạo database và bảng
"""
import mysql.connector
from mysql.connector import Error
import os
from dotenv import load_dotenv

load_dotenv()

# Database config
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "3306")
DB_USER = os.getenv("DB_USER", "root")
DB_PASSWORD = os.getenv("DB_PASSWORD", "")
DB_NAME = os.getenv("DB_NAME", "attendance_db")

def create_database():
    """Tạo database nếu chưa tồn tại"""
    try:
        # Kết nối MySQL server (không specify database)
        connection = mysql.connector.connect(
            host=DB_HOST,
            port=DB_PORT,
            user=DB_USER,
            password=DB_PASSWORD
        )

        if connection.is_connected():
            cursor = connection.cursor()

            # Tạo database
            cursor.execute(f"CREATE DATABASE IF NOT EXISTS {DB_NAME} CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci")
            print(f"✅ Database '{DB_NAME}' đã được tạo thành công!")

            # Chọn database
            cursor.execute(f"USE {DB_NAME}")

            # Tạo bảng students
            create_students_table = """
            CREATE TABLE IF NOT EXISTS students (
                student_id VARCHAR(20) PRIMARY KEY,
                full_name VARCHAR(100) NOT NULL,
                class_id VARCHAR(20) NOT NULL,
                face_encoding LONGBLOB,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                INDEX idx_class_id (class_id),
                INDEX idx_student_name (full_name)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
            """
            cursor.execute(create_students_table)
            print("✅ Bảng 'students' đã được tạo!")

            # Tạo bảng classes
            create_classes_table = """
            CREATE TABLE IF NOT EXISTS classes (
                class_id VARCHAR(20) PRIMARY KEY,
                class_name VARCHAR(100) NOT NULL,
                subject_name VARCHAR(100) NOT NULL,
                lecturer_name VARCHAR(100) NOT NULL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                INDEX idx_class_name (class_name),
                INDEX idx_lecturer (lecturer_name)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
            """
            cursor.execute(create_classes_table)
            print("✅ Bảng 'classes' đã được tạo!")

            # Tạo bảng attendance (bổ sung cho hệ thống điểm danh)
            create_attendance_table = """
            CREATE TABLE IF NOT EXISTS attendance (
                id INT AUTO_INCREMENT PRIMARY KEY,
                student_id VARCHAR(20) NOT NULL,
                class_id VARCHAR(20) NOT NULL,
                attendance_date DATE NOT NULL,
                attendance_time TIME NOT NULL,
                status ENUM('present', 'absent', 'late') DEFAULT 'present',
                recognition_confidence FLOAT DEFAULT NULL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (student_id) REFERENCES students(student_id) ON DELETE CASCADE,
                FOREIGN KEY (class_id) REFERENCES classes(class_id) ON DELETE CASCADE,
                UNIQUE KEY unique_attendance (student_id, class_id, attendance_date),
                INDEX idx_date (attendance_date),
                INDEX idx_status (status)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
            """
            cursor.execute(create_attendance_table)
            print("✅ Bảng 'attendance' đã được tạo!")

            print("\n🎉 Tất cả bảng đã được tạo thành công!")
            print("📊 Cấu trúc database:")
            print("   - students: Thông tin sinh viên")
            print("   - classes: Thông tin lớp học")
            print("   - attendance: Lịch sử điểm danh")

    except Error as e:
        print(f"❌ Lỗi MySQL: {e}")
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()

def test_connection():
    """Test kết nối database"""
    try:
        connection = mysql.connector.connect(
            host=DB_HOST,
            port=DB_PORT,
            user=DB_USER,
            password=DB_PASSWORD,
            database=DB_NAME
        )

        if connection.is_connected():
            print("✅ Kết nối MySQL thành công!")

            cursor = connection.cursor()
            cursor.execute("SHOW TABLES")
            tables = cursor.fetchall()

            print("📋 Các bảng trong database:")
            for table in tables:
                print(f"   - {table[0]}")

    except Error as e:
        print(f"❌ Lỗi kết nối: {e}")
        print("💡 Kiểm tra lại thông tin trong file .env")
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()

if __name__ == "__main__":
    print("🚀 Khởi tạo database MySQL cho hệ thống điểm danh HUTECH")
    print("=" * 60)
    print(f"Host: {DB_HOST}")
    print(f"Port: {DB_PORT}")
    print(f"User: {DB_USER}")
    print(f"Database: {DB_NAME}")
    print("=" * 60)

    # Tạo database và tables
    create_database()

    print("\n" + "=" * 60)
    # Test connection
    test_connection()

    print("\n✨ Hoàn thành! Bây giờ bạn có thể chạy FastAPI app với:")
    print("   python -m uvicorn app.main:app --reload")
