# app/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
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

@app.get("/")
async def root():
    return {"message": "Face Recognition Attendance System API v2.0"}

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "face-recognition-api"}