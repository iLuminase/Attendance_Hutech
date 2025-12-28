from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy import text
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import Session

from models.student import Student
from models.session_model import Session as SessionModel
from models.class_model import Class as ClassModel
from models.session_class_model import SessionClass
from schemas.attendance_schema import (
    AttendanceCheckinByFaceResponse,
    AttendanceRecordResponse,
)
from services.database_service import db_service
from services.face_service import face_service

router = APIRouter(prefix="/api/attendance", tags=["attendance"])


def _status_to_vi(raw: Optional[str]) -> Optional[str]:
    """Chuẩn hoá status hiển thị tiếng Việt (đồng bộ UI)."""
    if raw is None:
        return None
    s = str(raw).strip()
    if not s:
        return None

    key = s.upper()
    if key == "ON_TIME":
        return "Đúng giờ"
    if key == "LATE":
        return "Trễ"
    if key == "ABSENT":
        return "Vắng"

    # schema enum kiểu setup_database.py: present/late/absent
    low = s.lower()
    if low == "present":
        return "Đúng giờ"
    if low == "late":
        return "Trễ"
    if low == "absent":
        return "Vắng"

    return s


def _normalize_status_for_date_schema(raw: str) -> str:
    """Schema attendance_date/time chỉ nhận: present/late/absent."""
    if not raw:
        return "present"
    key = str(raw).strip().upper()
    if key == "ON_TIME":
        return "present"
    if key == "LATE":
        return "late"
    if key == "ABSENT":
        return "absent"

    low = str(raw).strip().lower()
    if low in {"present", "late", "absent"}:
        return low
    return "present"


def _parse_class_ids(raw: Optional[str]) -> List[str]:
    """Parse chuỗi class_ids dạng 'CSE101,CSE102' thành list đã trim."""
    if not raw:
        return []
    return [x.strip() for x in raw.split(",") if x.strip()]


def _get_table_columns(db: Session, table_name: str) -> set[str]:
    """Lấy danh sách cột hiện có của table (để tương thích nhiều schema)."""
    rows = db.execute(text(f"SHOW COLUMNS FROM {table_name}"))
    return {row[0] for row in rows.fetchall()}


def _ensure_attendance_table(db: Session) -> None:
    """Đảm bảo có bảng attendance (tạo bằng SQLAlchemy nếu chưa có)."""
    try:
        db.execute(text("SELECT 1 FROM attendance LIMIT 1"))
    except Exception:
        # Tạo table từ Base metadata nếu thiếu
        from app.database import Base
        from services.database_service import db_service as _db
        Base.metadata.create_all(bind=_db.engine)


def _ensure_session_classes_table(db: Session) -> None:
    """Tạo table session_classes nếu chưa có (hỗ trợ 1 session nhiều lớp).

    Tránh tự set charset/collation để không lệch với bảng tham chiếu.
    Nếu schema cũ làm FK lỗi (errno 150) thì fallback tạo bảng không FK.
    """
    try:
        SessionClass.__table__.create(bind=db.get_bind(), checkfirst=True)
    except OperationalError as exc:
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


def _get_session_class_ids(db: Session, session_id: int) -> List[str]:
    """Lấy danh sách lớp tham dự của session từ DB."""
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


def _upsert_attendance_compatible(
    db: Session,
    *,
    student: Student,
    session_id: Optional[int],
    class_id: Optional[str],
    checkin_at: datetime,
    status: str,
    confidence: Optional[float],
) -> Optional[int]:
    """Ghi điểm danh theo schema hiện có của bảng attendance."""
    _ensure_attendance_table(db)

    cols = _get_table_columns(db, "attendance")

    # Ưu tiên schema kiểu setup_database.py: attendance_date + attendance_time
    if "attendance_date" in cols and "attendance_time" in cols:
        # class_id dạng string (mã lớp)
        cid_value: Any = class_id if class_id is not None else student.class_id
        cid_value = str(cid_value) if cid_value is not None else None

        # UNIQUE thường là (student_id, class_id, attendance_date)
        insert_sql = text(
            """
            INSERT INTO attendance (student_id, class_id, attendance_date, attendance_time, status, recognition_confidence)
            VALUES (:student_id, :class_id, :attendance_date, :attendance_time, :status, :confidence)
            ON DUPLICATE KEY UPDATE
                attendance_time = VALUES(attendance_time),
                status = VALUES(status),
                recognition_confidence = VALUES(recognition_confidence)
            """
        )
        db.execute(
            insert_sql,
            {
                "student_id": student.student_id,
                "class_id": cid_value,
                "attendance_date": checkin_at.date(),
                "attendance_time": checkin_at.time().replace(microsecond=0),
                "status": _normalize_status_for_date_schema(status),
                "confidence": confidence,
            },
        )
        db.commit()

        # Trả về id mới nhất (nếu có cột id)
        if "id" in cols:
            row = db.execute(
                text(
                    """
                    SELECT id FROM attendance
                    WHERE student_id = :student_id AND class_id = :class_id AND attendance_date = :attendance_date
                    """
                ),
                {
                    "student_id": student.student_id,
                    "class_id": cid_value,
                    "attendance_date": checkin_at.date(),
                },
            ).fetchone()
            return int(row[0]) if row else None
        return None

    # Schema kiểu ORM: checkin_time (+ session_id)
    # Nếu bảng có session_id thì dùng unique (student_id, session_id) nếu tồn tại
    has_session_id = "session_id" in cols
    has_checkin_time = "checkin_time" in cols

    if not has_checkin_time:
        raise HTTPException(status_code=500, detail="Attendance table schema unsupported")

    # Kiểm tra đã điểm danh trong cùng session hoặc cùng ngày
    if has_session_id and session_id is not None:
        existing = db.execute(
            text(
                """
                SELECT attendance_id FROM attendance
                WHERE student_id = :student_id AND session_id = :session_id
                LIMIT 1
                """
            ),
            {"student_id": student.student_id, "session_id": session_id},
        ).fetchone()
    else:
        # fallback: theo ngày
        existing = db.execute(
            text(
                """
                SELECT attendance_id FROM attendance
                WHERE student_id = :student_id AND DATE(checkin_time) = :today
                LIMIT 1
                """
            ),
            {"student_id": student.student_id, "today": checkin_at.date()},
        ).fetchone()

    if existing:
        attendance_id = int(existing[0])
        db.execute(
            text(
                """
                UPDATE attendance
                SET checkin_time = :checkin_time, status = :status
                WHERE attendance_id = :attendance_id
                """
            ),
            {
                "checkin_time": checkin_at,
                "status": status,
                "attendance_id": attendance_id,
            },
        )
        db.commit()
        return attendance_id

    # Insert mới
    fields: List[str] = ["student_id", "checkin_time", "status"]
    params: Dict[str, Any] = {
        "student_id": student.student_id,
        "checkin_time": checkin_at,
        "status": status,
    }

    if has_session_id and session_id is not None:
        fields.append("session_id")
        params["session_id"] = session_id

    insert = text(
        f"INSERT INTO attendance ({', '.join(fields)}) VALUES ({', '.join(':'+f for f in fields)})"
    )
    db.execute(insert, params)
    db.commit()

    # Lấy id nếu có
    id_col = "attendance_id" if "attendance_id" in cols else ("id" if "id" in cols else None)
    if id_col:
        row = db.execute(text("SELECT LAST_INSERT_ID()"))
        val = row.fetchone()[0]
        return int(val) if val is not None else None
    return None


@router.post("/checkin-by-face", response_model=AttendanceCheckinByFaceResponse)
async def checkin_by_face(
    file: UploadFile = File(...),
    session_id: Optional[int] = Form(None),
    class_id: Optional[str] = Form(None),
    class_ids: Optional[str] = Form(None),
    db: Session = Depends(db_service.get_db),
):
    """Điểm danh bằng camera: detect → encode → compare → save."""
    try:
        image_bytes = await file.read()

        img = face_service.preprocess_image(image_bytes)
        if img is None:
            raise HTTPException(status_code=400, detail="Invalid image format")

        faces = face_service.detect_faces(img)
        if not faces:
            return AttendanceCheckinByFaceResponse(
                success=True,
                faces_count=0,
                recognized_count=0,
                attendances_created=0,
                attendances=[],
                message="No faces detected",
            )

        students = db.query(Student).filter(Student.face_encoding.isnot(None)).all()

        attendances: List[AttendanceRecordResponse] = []
        created_count = 0
        checkin_at = datetime.now()

        # class_ids (multi) ưu tiên hơn class_id (single)
        allowed_class_ids = set(_parse_class_ids(class_ids))

        # Nếu có session_id: dùng để tính trạng thái ON_TIME/LATE (cho phép trễ 15p)
        session_row: Optional[SessionModel] = None
        if session_id is not None:
            session_row = db.query(SessionModel).filter(SessionModel.session_id == session_id).first()

        # Nếu chọn session nhưng không truyền class_id(s): auto giới hạn theo session_classes (nếu có)
        if session_id is not None and not allowed_class_ids and class_id is None:
            session_cids = _get_session_class_ids(db, session_id)
            if session_cids:
                allowed_class_ids = set(session_cids)

        for face in faces:
            face_encoding = face_service.extract_face_encoding(img, face)
            if face_encoding is None:
                continue

            best_match: Optional[Student] = None
            best_similarity = 0.0

            for student in students:
                student_encoding = student.get_face_encoding()
                if student_encoding is None:
                    continue

                is_match, similarity = face_service.compare_faces(
                    face_encoding, student_encoding, threshold=0.7
                )

                if is_match and similarity > best_similarity:
                    best_similarity = similarity
                    best_match = student

            if not best_match:
                continue

            # Tính status
            status_value = "present"
            if session_row is not None and session_row.session_date and session_row.start_time:
                # Đúng giờ nếu checkin <= start + 15 phút
                session_start = datetime.combine(session_row.session_date, session_row.start_time)
                late_after = session_start.timestamp() + 15 * 60
                status_value = "ON_TIME" if checkin_at.timestamp() <= late_after else "LATE"

            # Xác định lớp sẽ ghi điểm danh
            effective_class_id: Optional[str] = None

            # Nếu chọn nhiều lớp: chỉ ghi nếu class_id của SV nằm trong danh sách
            if allowed_class_ids:
                if best_match.class_id is None:
                    continue
                student_cid = str(best_match.class_id)
                if student_cid not in allowed_class_ids:
                    continue
                effective_class_id = student_cid
            else:
                # Chọn 1 lớp (tùy chọn). Nếu truyền class_id thì chỉ ghi cho SV đúng lớp.
                if class_id is not None:
                    if best_match.class_id is None:
                        continue
                    if str(best_match.class_id) != str(class_id):
                        continue
                    effective_class_id = str(class_id)
                else:
                    # Không truyền lớp: mặc định dùng lớp của SV
                    effective_class_id = (
                        str(best_match.class_id) if best_match.class_id is not None else None
                    )

            # Lưu điểm danh
            attendance_id = _upsert_attendance_compatible(
                db,
                student=best_match,
                session_id=session_id,
                class_id=effective_class_id,
                checkin_at=checkin_at,
                status=status_value,
                confidence=float(best_similarity),
            )
            created_count += 1

            attendances.append(
                AttendanceRecordResponse(
                    attendance_id=attendance_id,
                    student_id=best_match.student_id,
                    student_name=best_match.name,
                    student_email=best_match.email,
                    class_id=effective_class_id
                    if effective_class_id is not None
                    else (str(best_match.class_id) if best_match.class_id is not None else None),
                    session_id=session_id,
                    session_date=session_row.session_date if session_row is not None else None,
                    start_time=session_row.start_time if session_row is not None else None,
                    end_time=session_row.end_time if session_row is not None else None,
                    checkin_time=checkin_at,
                    attendance_date=checkin_at.date(),
                    attendance_time=checkin_at.time().replace(microsecond=0),
                    status=_status_to_vi(status_value),
                    recognition_confidence=float(best_similarity),
                )
            )

        return AttendanceCheckinByFaceResponse(
            success=True,
            faces_count=len(faces),
            recognized_count=len(attendances),
            attendances_created=created_count,
            attendances=attendances,
            message=f"Checked in {len(attendances)} student(s)",
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error checkin by face: {str(e)}")


@router.get("/report", response_model=List[AttendanceRecordResponse])
def get_attendance_report(
    class_id: Optional[str] = None,
    class_ids: Optional[str] = None,
    date: Optional[str] = None,
    session_id: Optional[int] = None,
    db: Session = Depends(db_service.get_db),
):
    """Lấy dữ liệu điểm danh để báo cáo."""
    _ensure_attendance_table(db)
    cols = _get_table_columns(db, "attendance")

    # Ưu tiên báo cáo theo session_id (đầy đủ môn học + giờ học + vắng)
    if session_id is not None:
        requested_multi_class_ids = _parse_class_ids(class_ids)

        # Lấy thông tin session (giờ học) - class_id của session chỉ dùng để default/validate single-class
        session_info = db.execute(
            text(
                """
                SELECT s.session_id, s.class_id, s.session_date, s.start_time, s.end_time
                FROM sessions s
                WHERE s.session_id = :session_id
                LIMIT 1
                """
            ),
            {"session_id": session_id},
        ).fetchone()
        if not session_info:
            raise HTTPException(status_code=404, detail="Session not found")

        sid, cid, sdate, stime, etime = session_info

        # Giữ validate cũ cho trường hợp 1 lớp (không truyền class_ids)
        if not requested_multi_class_ids and class_id is not None and cid is not None:
            if str(cid) != str(class_id):
                raise HTTPException(status_code=400, detail="class_id không khớp với session")

        # Xác định danh sách lớp cần report
        target_class_ids: List[str] = []
        if requested_multi_class_ids:
            target_class_ids = requested_multi_class_ids
        elif class_id is not None:
            target_class_ids = [str(class_id)]
        else:
            # Nếu không truyền lớp: ưu tiên lấy theo session_classes (nhiều lớp)
            session_cids = _get_session_class_ids(db, sid)
            if session_cids:
                target_class_ids = session_cids
            elif cid is not None:
                # fallback legacy: sessions.class_id
                target_class_ids = [str(cid)]

        # Không có lớp để tính ABSENT => báo lỗi
        if not target_class_ids:
            raise HTTPException(
                status_code=400,
                detail="Cần truyền class_id hoặc class_ids khi report theo session nhiều lớp",
            )

        # Unique giữ thứ tự
        seen: set[str] = set()
        target_class_ids = [x for x in target_class_ids if not (x in seen or seen.add(x))]

        # Build IN params an toàn cho SQL text
        cid_placeholders: List[str] = []
        base_params: Dict[str, Any] = {
            "session_id": sid,
            "session_date": sdate,
            "start_time": stime,
            "end_time": etime,
        }
        for idx, cid_item in enumerate(target_class_ids):
            k = f"cid{idx}"
            cid_placeholders.append(f":{k}")
            base_params[k] = str(cid_item)

        in_sql = ", ".join(cid_placeholders)

        # Nếu attendance có schema checkin_time + session_id
        if "session_id" in cols and "checkin_time" in cols:
            conf_select = "a.recognition_confidence" if "recognition_confidence" in cols else "NULL"
            rows = db.execute(
                text(
                    f"""
                    SELECT
                        a.attendance_id,
                        st.student_id,
                        st.name as student_name,
                        st.email as student_email,
                        st.class_id as class_id,
                        c.class_name as class_name,
                        c.subject_name as subject_name,
                        :session_id as session_id,
                        :session_date as session_date,
                        :start_time as start_time,
                        :end_time as end_time,
                        a.checkin_time,
                        CASE
                            WHEN a.attendance_id IS NULL THEN 'ABSENT'
                            WHEN a.checkin_time <= (TIMESTAMP(:session_date, :start_time) + INTERVAL 15 MINUTE) THEN 'ON_TIME'
                            ELSE 'LATE'
                        END as status,
                        {conf_select} as recognition_confidence
                    FROM students st
                    LEFT JOIN classes c ON c.class_id = st.class_id
                    LEFT JOIN attendance a
                        ON a.student_id = st.student_id AND a.session_id = :session_id
                    WHERE st.class_id IN ({in_sql})
                    ORDER BY st.class_id ASC, st.student_id ASC
                    """
                ),
                base_params,
            ).fetchall()
        # Nếu attendance dùng schema attendance_date + attendance_time (setup_database.py)
        elif "attendance_date" in cols and "attendance_time" in cols and "class_id" in cols:
            conf_select = "a.recognition_confidence" if "recognition_confidence" in cols else "NULL"
            # id có thể là 'id'
            rows = db.execute(
                text(
                    f"""
                    SELECT
                        a.id as attendance_id,
                        st.student_id,
                        st.name as student_name,
                        st.email as student_email,
                        st.class_id as class_id,
                        c.class_name as class_name,
                        c.subject_name as subject_name,
                        :session_id as session_id,
                        :session_date as session_date,
                        :start_time as start_time,
                        :end_time as end_time,
                        CASE
                            WHEN a.id IS NULL THEN NULL
                            ELSE TIMESTAMP(a.attendance_date, a.attendance_time)
                        END as checkin_time,
                        CASE
                            WHEN a.id IS NULL THEN 'ABSENT'
                            WHEN TIMESTAMP(a.attendance_date, a.attendance_time) <= (TIMESTAMP(:session_date, :start_time) + INTERVAL 15 MINUTE) THEN 'ON_TIME'
                            ELSE 'LATE'
                        END as status,
                        {conf_select} as recognition_confidence
                    FROM students st
                    LEFT JOIN classes c ON c.class_id = st.class_id
                    LEFT JOIN attendance a
                        ON a.student_id = st.student_id
                        AND a.class_id = st.class_id
                        AND a.attendance_date = :session_date
                    WHERE st.class_id IN ({in_sql})
                    ORDER BY st.class_id ASC, st.student_id ASC
                    """
                ),
                base_params,
            ).fetchall()
        else:
            raise HTTPException(status_code=400, detail="Attendance schema không hỗ trợ report theo session")

        result: List[AttendanceRecordResponse] = []
        for r in rows:
            result.append(
                AttendanceRecordResponse(
                    attendance_id=r[0],
                    student_id=r[1],
                    student_name=r[2],
                    student_email=r[3],
                    class_id=r[4],
                    class_name=r[5],
                    subject_name=r[6],
                    session_id=r[7],
                    session_date=r[8],
                    start_time=r[9],
                    end_time=r[10],
                    checkin_time=r[11],
                    status=_status_to_vi(r[12]),
                    recognition_confidence=r[13],
                )
            )
        return result

    where: List[str] = []
    params: Dict[str, Any] = {}

    # schema date/time
    if "attendance_date" in cols:
        if date:
            where.append("a.attendance_date = :attendance_date")
            params["attendance_date"] = date
        if class_id is not None and "class_id" in cols:
            where.append("a.class_id = :class_id")
            params["class_id"] = class_id

        where_sql = ("WHERE " + " AND ".join(where)) if where else ""

        rows = db.execute(
            text(
                f"""
                SELECT
                    a.id as attendance_id,
                    a.student_id,
                    s.name as student_name,
                    s.email as student_email,
                    s.class_id as student_class_id,
                    a.class_id as attendance_class_id,
                    a.attendance_date,
                    a.attendance_time,
                    a.status,
                    a.recognition_confidence
                FROM attendance a
                LEFT JOIN students s ON s.student_id = a.student_id
                {where_sql}
                ORDER BY a.attendance_date DESC, a.attendance_time DESC
                """
            ),
            params,
        ).fetchall()

        result: List[AttendanceRecordResponse] = []
        for r in rows:
            result.append(
                AttendanceRecordResponse(
                    attendance_id=r[0],
                    student_id=r[1],
                    student_name=r[2],
                    student_email=r[3],
                    class_id=r[5] if r[5] is not None else r[4],
                    attendance_date=r[6],
                    attendance_time=r[7],
                    status=_status_to_vi(r[8]),
                    recognition_confidence=r[9],
                )
            )
        return result

    # schema checkin_time
    if date:
        where.append("DATE(a.checkin_time) = :today")
        params["today"] = date

    where_sql = ("WHERE " + " AND ".join(where)) if where else ""

    rows = db.execute(
        text(
            f"""
            SELECT
                a.attendance_id,
                a.student_id,
                s.name as student_name,
                s.email as student_email,
                s.class_id as class_id,
                a.session_id,
                a.checkin_time,
                a.status
            FROM attendance a
            LEFT JOIN students s ON s.student_id = a.student_id
            {where_sql}
            ORDER BY a.checkin_time DESC
            """
        ),
        params,
    ).fetchall()

    result: List[AttendanceRecordResponse] = []
    for r in rows:
        result.append(
            AttendanceRecordResponse(
                attendance_id=r[0],
                student_id=r[1],
                student_name=r[2],
                student_email=r[3],
                class_id=r[4],
                session_id=r[5],
                checkin_time=r[6],
                status=_status_to_vi(r[7]),
            )
        )
    return result
