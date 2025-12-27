import { HttpClient } from '@angular/common/http';
import { Injectable } from '@angular/core';
import { Observable } from 'rxjs';

import { apiBase } from './api-config';

export interface FaceBox {
  id: number;
  x: number;
  y: number;
  w: number;
  h: number;
  confidence?: number;
}

export interface RecognizedStudent {
  student_id: string;
  name: string;
  email?: string;
  class_id?: string | null;
  similarity?: number;
  face_box?: FaceBox;
}

export interface FaceRecognizeResponse {
  success: boolean;
  faces_count: number;
  faces: FaceBox[];
  recognized_count?: number;
  recognized_students: Array<RecognizedStudent | null>;
  message: string;
}

@Injectable({
  providedIn: 'root',
})
export class FaceService {
  constructor(private http: HttpClient) { }

  // 🧠 Nhận diện để lấy box + tên/MSSV
  recognize(file: Blob): Observable<FaceRecognizeResponse> {
    const baseUrl = apiBase('/api/face');
    const form = new FormData();
    form.append('file', file, 'frame.jpg');
    return this.http.post<FaceRecognizeResponse>(`${baseUrl}/recognize`, form);
  }
}
