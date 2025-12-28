# app/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
from sqlalchemy.exc import OperationalError

from app.database import engine
from models.session_class_model import SessionClass
from routers import student_router, class_router, session_router, face_router, attendance_router

app = FastAPI(
    title="Attendance System API",
    description="Face Recognition Attendance System",
    version="2.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(student_router.router, prefix="/api")
app.include_router(class_router.router, prefix="/api")
app.include_router(session_router.router, prefix="/api")
app.include_router(face_router.router)  # Already has /api prefix
app.include_router(attendance_router.router)  # Already has /api prefix


@app.on_event("startup")
def ensure_session_classes_table() -> None:
    """Đảm bảo bảng session_classes tồn tại trước khi API được gọi."""
    try:
        SessionClass.__table__.create(bind=engine, checkfirst=True)
    except OperationalError as exc:
        msg = str(getattr(exc, "orig", exc))
        if "errno: 150" not in msg and "Foreign key constraint" not in msg:
            raise

        # Fallback: tạo bảng không FK để tránh crash trên schema cũ
        with engine.begin() as conn:
            conn.execute(
                text(
                    """
                    CREATE TABLE IF NOT EXISTS session_classes (
                        session_id INT NOT NULL,
                        class_id VARCHAR(20) NOT NULL,
                        PRIMARY KEY (session_id, class_id),
                        INDEX idx_sc_session (session_id),
                        INDEX idx_sc_class (class_id)
                    ) ENGINE=InnoDB
                    """
                )
            )

@app.get("/")
async def root():
    return {"message": "Face Recognition Attendance System API v2.0"}

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "face-recognition-api"}