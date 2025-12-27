// Student Model Interface - Phù hợp với backend
export interface Student {
    student_id: string;
    name: string;
    email: string;
    phone?: string;
    class_id: string;
    face_encoding?: string | null; // Can be string, binary data, or null
    face_encoding_version?: string | null;
    created_at: Date;
    updated_at: Date;
}

// DTO cho tạo sinh viên mới
export interface CreateStudentDto {
    student_id: string;
    name: string;
    email: string;
    phone?: string;
    class_id: string;
}

// DTO cho cập nhật sinh viên
export interface UpdateStudentDto extends Partial<CreateStudentDto> {
    student_id: string;
}

// API Response Types
export interface ApiResponse<T> {
    success: boolean;
    data: T;
    message?: string;
    errors?: string[];
}

export interface PaginatedResponse<T> {
    data: T[];
    total: number;
    page: number;
    limit: number;
    totalPages: number;
}

// Filter/Search params - Đơn giản hóa theo backend
export interface StudentFilter {
    search?: string;
    class_id?: string;
}