# 🎓 Hutech Attendance System

Hệ thống điểm danh sử dụng nhận diện khuôn mặt cho trường Đại học Công nghệ TP.HCM (HUTECH)

## 🚀 Tính năng

### Frontend (Angular)
- 🖥️ Giao diện quản lý học sinh, lớp học
- 📊 Dashboard thống kê điểm danh
- 📱 Responsive design cho mobile/desktop
- 🔒 Authentication và phân quyền

### Backend (FastAPI + Python)
- 🤖 **Face Recognition**: Nhận diện khuôn mặt với OpenCV
- 🗄️ **Database**: MySQL với SQLAlchemy ORM
- 🚦 **Multi-tier Detection**: Haar Cascade → Edge Detection → Fallback
- 📡 **REST API**: FastAPI với auto documentation
- 🔐 **Security**: JWT authentication, input validation

## 🏗️ Cấu trúc project

```
Attendance_Hutech/
├── attendance_backend/          # FastAPI Backend
│   ├── app/
│   │   ├── main.py             # FastAPI app entry
│   │   └── database.py         # Database config
│   ├── models/                 # SQLAlchemy models
│   ├── routers/                # API endpoints
│   ├── services/               # Business logic
│   │   └── face_service.py     # Face recognition
│   ├── schemas/                # Pydantic schemas
│   └── requirements.txt
├── frontend/                   # Angular Frontend (if exists)
└── README.md
```

## ⚡ Quick Start

### Backend Setup
```bash
cd attendance_backend

# Create virtual environment
python -m venv venv
venv\Scripts\activate  # Windows
# source venv/bin/activate  # Linux/Mac

# Install dependencies
pip install -r requirements.txt

# Setup database
python setup_database.py

# Start server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### API Documentation
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## 🎯 API Endpoints

### Students
- GET /students/ - Danh sách học sinh
- POST /students/ - Tạo học sinh mới  
- PUT /students/{id} - Cập nhật thông tin
- POST /students/{id}/upload-face - Upload ảnh khuôn mặt

### Face Recognition
- POST /api/face/detect - Phát hiện khuôn mặt
- POST /api/face/recognize - Nhận diện học sinh
- POST /api/face/recognize-with-image - Nhận diện + ảnh kết quả

### Classes & Sessions
- GET /classes/ - Quản lý lớp học
- POST /sessions/ - Tạo buổi học
- POST /sessions/{id}/attendance - Điểm danh

## 🧠 Face Recognition Tech

### Detection Strategy
1. **Primary**: Haar Cascade (3 sensitivity levels)
2. **Fallback**: Edge-based contour detection  
3. **Last Resort**: Center region extraction

### Performance
- Auto-resize images → max 800px width
- Face encoding: 1024 features (32x32 normalized)
- Similarity threshold: 0.8 correlation

## 🔧 Configuration

### Database (MySQL)
```python
DATABASE_URL = "mysql+pymysql://user:password@localhost/attendance_db"
```

### Environment Variables
```bash
DB_HOST=localhost
DB_USER=root
DB_PASSWORD=your_password
DB_NAME=attendance_db
```

## 📖 Documentation

- [Face Recognition API](attendance_backend/FACE_RECOGNITION.md)
- Backend API: /docs endpoint
- Database Schema: models/ directory

## 🤝 Contributing

1. Fork the repository
2. Create feature branch: git checkout -b feature/amazing-feature
3. Commit changes: git commit -m 'Add amazing feature'
4. Push branch: git push origin feature/amazing-feature
5. Open Pull Request

## 📄 License

MIT License - xem file [LICENSE](LICENSE)

## 🎓 About HUTECH

Dự án được phát triển cho Trường Đại học Công nghệ TP.HCM (HUTECH)
