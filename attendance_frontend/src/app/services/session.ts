import { HttpClient } from '@angular/common/http';
import { Injectable } from '@angular/core';
import { Observable } from 'rxjs';

import { SessionModel } from '../models/session.model';
import { apiBase } from './api-config';

@Injectable({
  providedIn: 'root',
})
export class SessionService {
  constructor(private http: HttpClient) { }

  // 📋 Lấy danh sách buổi học
  getSessions(): Observable<SessionModel[]> {
    const baseUrl = apiBase('/api/sessions');
    return this.http.get<SessionModel[]>(`${baseUrl}/`);
  }
}
