# 🎯 HUTECH Attendance System - MySQL Setup

Hệ thống điểm danh tự động sử dụng FastAPI + MySQL + AI Face Recognition

## 🚀 Quick Start

### 1. Cấu hình Database
Chỉnh sửa file `.env` với thông tin MySQL của bạn:
```dotenv
DB_HOST=localhost
DB_PORT=3306
DB_USER=root
DB_PASSWORD=your_password
DB_NAME=attendance_db
```

### 2. Cài đặt Dependencies
```bash
pip install -r requirements.txt
```

### 3. Tạo Database
```bash
python setup_database.py
```

### 4. Chạy Server
```bash
python -m uvicorn app.main:app --reload
```

### 5. Test Hệ Thống
```bash
python demo_mysql.py
```

## 📋 API Endpoints

- **GET /** - Trang chủ API
- **GET /health** - Kiểm tra tình trạng hệ thống  
- **GET /docs** - API Documentation (Swagger UI)

### Students
- **POST /students/** - Tạo sinh viên mới
- **GET /students/** - Lấy danh sách sinh viên
- **GET /students/{student_id}** - Lấy thông tin sinh viên
- **DELETE /students/{student_id}** - Xóa sinh viên

### Classes  
- **POST /classes/** - Tạo lớp học mới
- **GET /classes/** - Lấy danh sách lớp học
- **GET /classes/{class_id}** - Lấy thông tin lớp học

## 🏗️ Cấu Trúc Dự Án

```
attendance_backend/
├── app/
│   ├── __init__.py
│   ├── main.py          # FastAPI app chính
│   └── database.py      # Cấu hình database
├── models/
│   ├── __init__.py
│   ├── student.py       # Model sinh viên  
│   ├── student_schema.py # Schema sinh viên
│   ├── class_model.py   # Model lớp học
│   └── class_schema.py  # Schema lớp học
├── routers/
│   ├── __init__.py
│   ├── student_router.py # API sinh viên
│   └── class_router.py  # API lớp học
├── services/
│   ├── __init__.py
│   └── database_service.py # Service database
├── schemas/
│   └── __init__.py
├── .env                 # Cấu hình môi trường
├── requirements.txt     # Dependencies
├── setup_database.py    # Script tạo database
└── demo_mysql.py        # Script test hệ thống
```

## 📊 Database Schema

### Table: students
```sql
student_id VARCHAR(20) PRIMARY KEY
full_name VARCHAR(100) NOT NULL  
class_id VARCHAR(20) NOT NULL
face_encoding LONGBLOB -- Dành cho AI
created_at DATETIME DEFAULT CURRENT_TIMESTAMP
```

### Table: classes
```sql
class_id VARCHAR(20) PRIMARY KEY
class_name VARCHAR(100) NOT NULL
subject_name VARCHAR(100) NOT NULL  
lecturer_name VARCHAR(100) NOT NULL
created_at DATETIME DEFAULT CURRENT_TIMESTAMP
```

### Table: attendance  
```sql
id INT AUTO_INCREMENT PRIMARY KEY
student_id VARCHAR(20) FOREIGN KEY
class_id VARCHAR(20) FOREIGN KEY
attendance_date DATE NOT NULL
attendance_time TIME NOT NULL
status ENUM('present', 'absent', 'late')
recognition_confidence FLOAT -- Độ tin cậy AI
created_at DATETIME DEFAULT CURRENT_TIMESTAMP
```

## 🎯 Tính Năng

✅ **MySQL Connection Pooling** - Tối ưu kết nối  
✅ **Error Handling** - Xử lý lỗi đầy đủ  
✅ **Health Check** - Monitoring hệ thống  
✅ **API Documentation** - Swagger UI  
✅ **UTF-8 Support** - Hỗ trợ tiếng Việt  
✅ **Foreign Keys** - Ràng buộc dữ liệu  
✅ **Indexes** - Tối ưu performance  

## 🚨 Troubleshooting

### Database Connection Error
```
OperationalError: (2003, "Can't connect to MySQL server...")
```
**Giải pháp:**
1. Kiểm tra MySQL service đã chạy chưa
2. Xác thực thông tin trong `.env`
3. Test kết nối: `python -c "import mysql.connector; print('OK')"`

### Access Denied Error  
```
OperationalError: (1045, "Access denied for user...")
```
**Giải pháp:**
1. Kiểm tra username/password trong `.env`
2. Cấp quyền cho user MySQL

### Import Error
```
ModuleNotFoundError: No module named 'app.xxx'  
```
**Giải pháp:**
1. Chạy từ folder `attendance_backend/`
2. Kiểm tra file `__init__.py` đã tồn tại

## 📞 Hỗ Trợ

- **API Docs**: http://127.0.0.1:8000/docs
- **Health Check**: http://127.0.0.1:8000/health
- **Test Script**: `python demo_mysql.py`

---
*Developed for HUTECH University Attendance System*
