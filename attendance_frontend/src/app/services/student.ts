import { HttpClient } from '@angular/common/http';
import { Injectable } from '@angular/core';
import { BehaviorSubject, Observable } from 'rxjs';
import { catchError, map } from 'rxjs/operators';
import {
  CreateStudentDto,
  Student as StudentModel,
  UpdateStudentDto
} from '../models/student.model';
import { apiBase } from './api-config';

@Injectable({
  providedIn: 'root',
})
export class StudentService {
  private studentsSubject = new BehaviorSubject<StudentModel[]>([]);
  public students$ = this.studentsSubject.asObservable();

  constructor(private http: HttpClient) { }

  // 📋 GET - Lấy danh sách tất cả sinh viên
  getStudents(): Observable<StudentModel[]> {
    const baseUrl = apiBase('/api/students');
    return this.http.get<StudentModel[]>(`${baseUrl}/`)
      .pipe(
        map(students => {
          this.studentsSubject.next(students);
          return students;
        }),
        catchError(this.handleError)
      );
  }

  // 👤 GET - Lấy thông tin 1 sinh viên
  getStudent(student_id: string): Observable<StudentModel> {
    const baseUrl = apiBase('/api/students');
    return this.http.get<StudentModel>(`${baseUrl}/${student_id}`)
      .pipe(catchError(this.handleError));
  }

  // ➕ POST - Thêm sinh viên mới
  createStudent(studentData: CreateStudentDto): Observable<StudentModel> {
    const baseUrl = apiBase('/api/students');
    return this.http.post<StudentModel>(`${baseUrl}/`, studentData)
      .pipe(
        map(response => {
          this.refreshStudents();
          return response;
        }),
        catchError(this.handleError)
      );
  }

  // ✏️ PUT - Cập nhật sinh viên
  updateStudent(student_id: string, studentData: UpdateStudentDto): Observable<StudentModel> {
    const baseUrl = apiBase('/api/students');
    return this.http.put<StudentModel>(`${baseUrl}/${student_id}`, studentData)
      .pipe(
        map(response => {
          this.refreshStudents();
          return response;
        }),
        catchError(this.handleError)
      );
  }

  // 🗑️ DELETE - Xóa sinh viên
  deleteStudent(student_id: string): Observable<{ message: string }> {
    const baseUrl = apiBase('/api/students');
    return this.http.delete<{ message: string }>(`${baseUrl}/${student_id}`)
      .pipe(
        map(response => {
          this.refreshStudents();
          return response;
        }),
        catchError(this.handleError)
      );
  }

  // 📷 Upload ảnh khuôn mặt cho sinh viên (backend sẽ extract encoding)
  uploadFaceImage(student_id: string, file: File): Observable<any> {
    const baseUrl = apiBase('/api/students');
    const form = new FormData();
    form.append('file', file);
    return this.http.post<any>(`${baseUrl}/${student_id}/upload-face`, form)
      .pipe(catchError(this.handleError));
  }

  // ✅ Kiểm tra sinh viên có ảnh/encoding không
  hasFaceImage(student_id: string): Observable<{ student_id: string; has_face_image: boolean; has_face_encoding: boolean }> {
    const baseUrl = apiBase('/api/students');
    return this.http.get<{ student_id: string; has_face_image: boolean; has_face_encoding: boolean }>(
      `${baseUrl}/${student_id}/has-face-image`
    ).pipe(catchError(this.handleError));
  }




  // 🔄 Refresh danh sách sinh viên
  private refreshStudents(): void {
    this.getStudents().subscribe();
  }

  // 🔄 Refresh single student data
  refreshStudent(student_id: string): Observable<StudentModel> {
    return this.getStudent(student_id).pipe(
      map(student => {
        // Update the student in the current list
        const currentStudents = this.studentsSubject.value;
        const index = currentStudents.findIndex(s => s.student_id === student_id);
        if (index >= 0) {
          currentStudents[index] = student;
          this.studentsSubject.next([...currentStudents]);
        }
        return student;
      })
    );
  }

  // ❌ Error handler
  private handleError = (error: any): Observable<any> => {
    console.error('Student API Error:', error);
    throw error;
  }
}
