export interface AttendanceRecord {
    attendance_id?: number | null;
    student_id: string;
    student_name?: string | null;
    student_email?: string | null;
    class_id?: string | null;
    class_name?: string | null;
    subject_name?: string | null;
    session_id?: number | null;

    session_date?: string | null;
    start_time?: string | null;
    end_time?: string | null;

    // backend có thể trả 1 trong 2 kiểu thời gian
    checkin_time?: string | null;
    attendance_date?: string | null;
    attendance_time?: string | null;

    status?: string | null;
    recognition_confidence?: number | null;
}

export interface AttendanceCheckinByFaceResponse {
    success: boolean;
    faces_count: number;
    recognized_count: number;
    attendances_created: number;
    attendances: AttendanceRecord[];
    message: string;
}
