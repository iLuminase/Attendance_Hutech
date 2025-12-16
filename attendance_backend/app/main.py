import sys
from pathlib import Path
import os

# Thêm parent directory vào sys.path để import routers và services
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.insert(0, parent_dir)

from fastapi import FastAPI
from routers import student_router, class_router, session_router
from services.database_service import db_service
import logging


# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="HUTECH Attendance System",
    description="Hệ thống điểm danh tự động sử dụng nhận diện khuôn mặt",
    version="1.0.0"
)

@app.on_event("startup")
async def startup_event():
    """Khởi tạo khi app start"""
    logger.info("🚀 Starting HUTECH Attendance System...")

    # Test database connection
    if db_service.test_connection():
        # Tạo tables nếu chưa có
        db_service.create_tables()
        logger.info("✅ Database initialized successfully")
    else:
        logger.error("❌ Database connection failed on startup")

@app.get("/")
async def root():
    """API gốc"""
    return {
        "message": "HUTECH Attendance System API",
        "version": "1.0.0",
        "docs": "/docs"
    }

@app.get("/health")
async def health_check():
    """Kiểm tra tình trạng hệ thống"""
    db_health = db_service.health_check()
    return {
        "api_status": "running",
        "database": db_health
    }

# Include routers
app.include_router(student_router.router)
app.include_router(class_router.router)
app.include_router(session_router.router)