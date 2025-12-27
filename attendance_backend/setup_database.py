"""Script tạo database MySQL + tạo bảng + seed dữ liệu mẫu.

- Không dùng mysql-connector (tránh thiếu dependency), dùng pymysql (đã có trong requirements.txt).
- Đồng bộ theo models hiện tại: students(name/email/phone/class_id/face_encoding/face_image/...)
- Hỗ trợ 1 session nhiều lớp qua bảng session_classes.
"""

from __future__ import annotations

import os
from datetime import date, time
from typing import Any, Iterable, Tuple

import pymysql
from dotenv import load_dotenv

load_dotenv()


DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = int(os.getenv("DB_PORT", "3306"))
DB_USER = os.getenv("DB_USER", "root")
DB_PASSWORD = os.getenv("DB_PASSWORD", "")
DB_NAME = os.getenv("DB_NAME", "attendance_db")

# Nếu muốn tạo mới sạch (drop tables) thì set env RESET_DB=1
RESET_DB = os.getenv("RESET_DB", "0") == "1"


def _exec_many(cur: pymysql.cursors.Cursor, statements: Iterable[str]) -> None:
    for sql in statements:
        cur.execute(sql)


def create_database_and_tables() -> None:
    """Tạo DB + schema chuẩn để publish."""
    conn = pymysql.connect(
        host=DB_HOST,
        port=DB_PORT,
        user=DB_USER,
        password=DB_PASSWORD,
        charset="utf8mb4",
        autocommit=True,
    )
    try:
        with conn.cursor() as cur:
            cur.execute(
                f"CREATE DATABASE IF NOT EXISTS {DB_NAME} CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci"
            )
            cur.execute(f"USE {DB_NAME}")

            if RESET_DB:
                # Xoá theo thứ tự để không vướng FK
                _exec_many(
                    cur,
                    [
                        "SET FOREIGN_KEY_CHECKS = 0",
                        "DROP TABLE IF EXISTS attendance",
                        "DROP TABLE IF EXISTS session_classes",
                        "DROP TABLE IF EXISTS sessions",
                        "DROP TABLE IF EXISTS students",
                        "DROP TABLE IF EXISTS classes",
                        "SET FOREIGN_KEY_CHECKS = 1",
                    ],
                )

            # 1) classes
            cur.execute(
                """
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
            )

            # 2) students (đúng theo models/student.py)
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS students (
                    student_id VARCHAR(20) PRIMARY KEY,
                    name VARCHAR(100) NOT NULL,
                    email VARCHAR(100) UNIQUE,
                    phone VARCHAR(15),
                    class_id VARCHAR(20),
                    face_encoding LONGBLOB,
                    face_image LONGBLOB,
                    face_encoding_version VARCHAR(10) DEFAULT '1.0',
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                    INDEX idx_students_class_id (class_id),
                    INDEX idx_students_name (name),
                    CONSTRAINT fk_students_class FOREIGN KEY (class_id)
                        REFERENCES classes(class_id) ON DELETE SET NULL
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
                """
            )

            # 3) sessions (đúng theo models/session_model.py)
            # Lưu class_id để tương thích legacy (class đầu tiên). Multi-class dùng session_classes.
            cur.execute(
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

            # 4) session_classes (many-to-many)
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS session_classes (
                    session_id INT NOT NULL,
                    class_id VARCHAR(20) NOT NULL,
                    PRIMARY KEY (session_id, class_id),
                    INDEX idx_sc_class_id (class_id),
                    CONSTRAINT fk_sc_session FOREIGN KEY (session_id)
                        REFERENCES sessions(session_id) ON DELETE CASCADE,
                    CONSTRAINT fk_sc_class FOREIGN KEY (class_id)
                        REFERENCES classes(class_id) ON DELETE CASCADE
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
                """
            )

            # 5) attendance (schema date/time - tương thích attendance_router.py)
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS attendance (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    student_id VARCHAR(20) NOT NULL,
                    class_id VARCHAR(20) NOT NULL,
                    attendance_date DATE NOT NULL,
                    attendance_time TIME NOT NULL,
                    status ENUM('present', 'absent', 'late') DEFAULT 'present',
                    recognition_confidence FLOAT DEFAULT NULL,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    CONSTRAINT fk_att_student FOREIGN KEY (student_id)
                        REFERENCES students(student_id) ON DELETE CASCADE,
                    CONSTRAINT fk_att_class FOREIGN KEY (class_id)
                        REFERENCES classes(class_id) ON DELETE CASCADE,
                    UNIQUE KEY unique_attendance (student_id, class_id, attendance_date),
                    INDEX idx_att_date (attendance_date),
                    INDEX idx_att_status (status)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
                """
            )

        print("✅ Đã tạo database + tables thành công")
    finally:
        conn.close()


def seed_sample_data() -> None:
    """Insert dữ liệu mẫu (an toàn: dùng INSERT IGNORE)."""
    conn = pymysql.connect(
        host=DB_HOST,
        port=DB_PORT,
        user=DB_USER,
        password=DB_PASSWORD,
        database=DB_NAME,
        charset="utf8mb4",
        autocommit=True,
    )
    try:
        with conn.cursor() as cur:
            # Classes
            classes: Tuple[Tuple[Any, ...], ...] = (
                ("20DTHE4", "20DTHE4", "Nhập môn AI", "GV. Nguyễn Văn A"),
                ("20DTHE5", "20DTHE5", "Nhập môn AI", "GV. Nguyễn Văn A"),
            )
            cur.executemany(
                """
                INSERT IGNORE INTO classes (class_id, class_name, subject_name, lecturer_name)
                VALUES (%s, %s, %s, %s)
                """,
                classes,
            )

            # Students (không seed face_encoding/face_image)
            students: Tuple[Tuple[Any, ...], ...] = (
                ("SV001", "Nguyễn Minh Anh", "sv001@example.com", "0900000001", "20DTHE4"),
                ("SV002", "Trần Quốc Bảo", "sv002@example.com", "0900000002", "20DTHE4"),
                ("SV003", "Lê Thị Cẩm", "sv003@example.com", "0900000003", "20DTHE4"),
                ("SV101", "Phạm Gia Huy", "sv101@example.com", "0900000101", "20DTHE5"),
                ("SV102", "Võ Ngọc Lan", "sv102@example.com", "0900000102", "20DTHE5"),
            )
            cur.executemany(
                """
                INSERT IGNORE INTO students (student_id, name, email, phone, class_id)
                VALUES (%s, %s, %s, %s, %s)
                """,
                students,
            )

            # Tạo 1 session demo cho hôm nay (session multi-class)
            today = date.today()
            st = time(7, 30, 0)
            et = time(9, 30, 0)

            # Lấy session_id nếu đã có session cùng ngày/giờ (để tránh tạo nhiều lần)
            cur.execute(
                """
                SELECT session_id FROM sessions
                WHERE session_date = %s AND start_time = %s AND end_time = %s
                LIMIT 1
                """,
                (today, st, et),
            )
            row = cur.fetchone()
            if row:
                session_id = int(row[0])
            else:
                # class_id legacy = lớp đầu tiên
                cur.execute(
                    """
                    INSERT INTO sessions (class_id, session_date, start_time, end_time)
                    VALUES (%s, %s, %s, %s)
                    """,
                    ("20DTHE4", today, st, et),
                )
                session_id = int(cur.lastrowid)

            # Map session -> 2 classes
            cur.executemany(
                """
                INSERT IGNORE INTO session_classes (session_id, class_id)
                VALUES (%s, %s)
                """,
                ((session_id, "20DTHE4"), (session_id, "20DTHE5")),
            )

        print("✅ Đã seed dữ liệu mẫu")
    finally:
        conn.close()


def main() -> None:
    print("🚀 Setup database MySQL (publish)")
    print("=" * 60)
    print(f"Host: {DB_HOST}")
    print(f"Port: {DB_PORT}")
    print(f"User: {DB_USER}")
    print(f"Database: {DB_NAME}")
    print(f"RESET_DB: {'1' if RESET_DB else '0'}")
    print("=" * 60)

    create_database_and_tables()
    seed_sample_data()

    print("\n✨ Hoàn thành")
    print("- Chạy backend: python -m uvicorn app.main:app --host 0.0.0.0 --port 8000")


if __name__ == "__main__":
    main()
