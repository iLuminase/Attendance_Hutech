import { HttpClient, HttpParams } from '@angular/common/http';
import { Injectable } from '@angular/core';
import { Observable } from 'rxjs';

import {
    AttendanceCheckinByFaceResponse,
    AttendanceRecord,
} from '../models/attendance.model';

import { apiBase } from './api-config';

@Injectable({
    providedIn: 'root',
})
export class AttendanceService {
    constructor(private http: HttpClient) { }

    // 📷 Điểm danh bằng ảnh camera
    checkinByFace(
        file: Blob,
        sessionId?: number,
        classId?: string,
        classIds?: string[],
    ): Observable<AttendanceCheckinByFaceResponse> {
        const baseUrl = apiBase('/api/attendance');
        const form = new FormData();
        form.append('file', file, 'frame.jpg');

        if (sessionId !== undefined && sessionId !== null) {
            form.append('session_id', String(sessionId));
        }

        // Multi class ưu tiên hơn single class
        if (classIds && classIds.length) {
            form.append('class_ids', classIds.join(','));
        } else if (classId !== undefined && classId !== null) {
            form.append('class_id', String(classId));
        }

        return this.http.post<AttendanceCheckinByFaceResponse>(`${baseUrl}/checkin-by-face`, form);
    }

    // 📊 Lấy dữ liệu báo cáo
    getReport(date?: string, classId?: string, sessionId?: number): Observable<AttendanceRecord[]> {
        const baseUrl = apiBase('/api/attendance');
        let params = new HttpParams();
        if (date) params = params.set('date', date);
        if (classId !== undefined && classId !== null) params = params.set('class_id', String(classId));
        if (sessionId !== undefined && sessionId !== null) params = params.set('session_id', String(sessionId));

        return this.http.get<AttendanceRecord[]>(`${baseUrl}/report`, { params });
    }
}
