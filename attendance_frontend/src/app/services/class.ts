import { HttpClient } from '@angular/common/http';
import { Injectable } from '@angular/core';
import { Observable } from 'rxjs';

import { ClassesListResponse, ClassModel } from '../models/class.model';
import { apiBase } from './api-config';

@Injectable({
  providedIn: 'root',
})
export class ClassService {
  constructor(private http: HttpClient) { }

  // 📋 Lấy danh sách lớp học
  getClasses(): Observable<ClassesListResponse> {
    const baseUrl = apiBase('/api/classes');
    return this.http.get<ClassesListResponse>(`${baseUrl}/`);
  }

  // 📋 Lấy chi tiết 1 lớp
  getClass(classId: string): Observable<ClassModel> {
    const baseUrl = apiBase('/api/classes');
    return this.http.get<ClassModel>(`${baseUrl}/${classId}`);
  }
}
