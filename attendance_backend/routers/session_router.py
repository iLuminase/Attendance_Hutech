import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import text
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import Session as DBSession
from typing import List, Optional
from app.database import SessionLocal
from models.session_model import Session as SessionModel
from models.session_class_model import SessionClass
from schemas.session_schema import SessionCreate, SessionResponse, SessionUpdate

router = APIRouter(prefix="/sessions", tags=["Sessions"])


def _ensure_session_classes_table(db: DBSession) -> None:
    """Tạo table session_classes nếu chưa có (hỗ trợ 1 session nhiều lớp).

    Lưu ý: Không tự set charset/collation ở đây để tránh lệch so với bảng tham chiếu,
    vì MySQL yêu cầu 2 cột FK (string) phải cùng collation/charset.
    """
    try:
        # Tạo theo metadata của SQLAlchemy (thường sẽ dùng default của DB)
        SessionClass.__table__.create(bind=db.get_bind(), checkfirst=True)
    except OperationalError as exc:
        # Nếu FK vẫn bị lỗi do schema cũ (engine/collation), fallback tạo bảng không FK
        db.rollback()
        msg = str(getattr(exc, "orig", exc))
        if "errno: 150" not in msg and "Foreign key constraint" not in msg:
            raise

        db.execute(
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
        db.commit()


def _normalize_class_ids(class_id: Optional[str], class_ids: Optional[List[str]]) -> List[str]:
    """Chuẩn hoá danh sách lớp: ưu tiên class_ids, fallback class_id."""
    if class_ids:
        items = [str(x).strip() for x in class_ids if str(x).strip()]
    elif class_id:
        items = [str(class_id).strip()]
    else:
        items = []

    # unique giữ thứ tự
    seen = set()
    return [x for x in items if not (x in seen or seen.add(x))]


def _get_class_ids_for_session(db: DBSession, session_id: int) -> List[str]:
    """Lấy list class_ids của session từ session_classes."""
    _ensure_session_classes_table(db)
    rows = db.execute(
        text(
            """
            SELECT class_id
            FROM session_classes
            WHERE session_id = :session_id
            ORDER BY class_id ASC
            """
        ),
        {"session_id": session_id},
    ).fetchall()
    return [str(r[0]) for r in rows]

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/", response_model=SessionResponse)
def create_session(data: SessionCreate, db: DBSession = Depends(get_db)):
    target_class_ids = _normalize_class_ids(data.class_id, data.class_ids)
    if not target_class_ids:
        raise HTTPException(status_code=400, detail="Cần truyền class_id hoặc class_ids")

    payload = data.dict(exclude={"class_ids"})
    # Giữ tương thích schema hiện tại: sessions.class_id lưu lớp đầu tiên
    payload["class_id"] = target_class_ids[0]

    db_session = SessionModel(**payload)
    db.add(db_session)
    db.commit()
    db.refresh(db_session)

    _ensure_session_classes_table(db)
    # Upsert danh sách lớp tham dự
    for cid in target_class_ids:
        db.execute(
            text(
                """
                INSERT IGNORE INTO session_classes (session_id, class_id)
                VALUES (:session_id, :class_id)
                """
            ),
            {"session_id": db_session.session_id, "class_id": cid},
        )
    db.commit()

    # Trả về có class_ids
    resp = SessionResponse.model_validate(db_session)
    resp.class_ids = target_class_ids
    return resp

@router.get("/", response_model=List[SessionResponse])
def get_all_sessions(db: DBSession = Depends(get_db)):
    sessions = db.query(SessionModel).all()
    result: List[SessionResponse] = []
    for s in sessions:
        class_ids = _get_class_ids_for_session(db, s.session_id)
        if not class_ids and getattr(s, "class_id", None):
            class_ids = [str(s.class_id)]
        resp = SessionResponse.model_validate(s)
        resp.class_ids = class_ids
        result.append(resp)
    return result

@router.get("/{session_id}", response_model=SessionResponse)
def get_session(session_id: int, db: DBSession = Depends(get_db)):
    session = db.query(SessionModel).filter(SessionModel.session_id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    class_ids = _get_class_ids_for_session(db, session_id)
    if not class_ids and getattr(session, "class_id", None):
        class_ids = [str(session.class_id)]
    resp = SessionResponse.model_validate(session)
    resp.class_ids = class_ids
    return resp

@router.put("/{session_id}", response_model=SessionResponse)
def update_session(session_id: int, data: SessionUpdate, db: DBSession = Depends(get_db)):
    session = db.query(SessionModel).filter(SessionModel.session_id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    update_payload = data.dict(exclude_unset=True)
    target_class_ids: Optional[List[str]] = None
    if "class_ids" in update_payload or "class_id" in update_payload:
        target_class_ids = _normalize_class_ids(
            update_payload.get("class_id"), update_payload.get("class_ids")
        )
        if not target_class_ids:
            raise HTTPException(status_code=400, detail="class_id/class_ids không hợp lệ")

        # sessions.class_id giữ lớp đầu tiên
        update_payload["class_id"] = target_class_ids[0]
        update_payload.pop("class_ids", None)

    for field, value in update_payload.items():
        setattr(session, field, value)
    
    db.commit()
    db.refresh(session)

    if target_class_ids is not None:
        _ensure_session_classes_table(db)
        db.execute(
            text("DELETE FROM session_classes WHERE session_id = :session_id"),
            {"session_id": session_id},
        )
        for cid in target_class_ids:
            db.execute(
                text(
                    """
                    INSERT IGNORE INTO session_classes (session_id, class_id)
                    VALUES (:session_id, :class_id)
                    """
                ),
                {"session_id": session_id, "class_id": cid},
            )
        db.commit()

    class_ids = _get_class_ids_for_session(db, session_id)
    if not class_ids and getattr(session, "class_id", None):
        class_ids = [str(session.class_id)]
    resp = SessionResponse.model_validate(session)
    resp.class_ids = class_ids
    return resp

@router.delete("/{session_id}")
def delete_session(session_id: int, db: DBSession = Depends(get_db)):
    session = db.query(SessionModel).filter(SessionModel.session_id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    db.delete(session)
    db.commit()
    return {"message": "Session deleted successfully"}
