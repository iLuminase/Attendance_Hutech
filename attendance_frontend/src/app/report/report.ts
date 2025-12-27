import { CommonModule } from '@angular/common';
import { Component } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { MatButtonModule } from '@angular/material/button';
import { MatCardModule } from '@angular/material/card';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatIconModule } from '@angular/material/icon';
import { MatInputModule } from '@angular/material/input';
import { MatProgressSpinnerModule } from '@angular/material/progress-spinner';
import { MatSelectModule } from '@angular/material/select';
import { MatTableModule } from '@angular/material/table';

import { AttendanceRecord } from '../models/attendance.model';
import { SessionModel } from '../models/session.model';
import { AttendanceService } from '../services/attendance';
import { SessionService } from '../services/session';

@Component({
  selector: 'app-report',
  imports: [
    CommonModule,
    FormsModule,
    MatCardModule,
    MatFormFieldModule,
    MatInputModule,
    MatButtonModule,
    MatTableModule,
    MatIconModule,
    MatProgressSpinnerModule,
    MatSelectModule,
  ],
  templateUrl: './report.html',
  styleUrl: './report.css',
})
export class Report {
  date = new Date().toISOString().slice(0, 10);
  sessions: SessionModel[] = [];
  selectedSessionId: number | null = null;
  data: AttendanceRecord[] = [];
  message = '';
  isLoading = false;

  displayedColumns: string[] = [
    'student_id',
    'student_name',
    'class',
    'subject',
    'session_time',
    'checkin',
    'status',
  ];

  constructor(
    private attendanceService: AttendanceService,
    private sessionService: SessionService,
  ) {
    this.sessionService.getSessions().subscribe({
      next: (rows) => {
        this.sessions = rows || [];
        // Mặc định chọn session đầu tiên của hôm nay (nếu có)
        const today = this.date;
        const todaySessions = this.sessions.filter((s) => s.session_date === today);
        if (this.selectedSessionId === null && todaySessions.length) {
          this.selectedSessionId = todaySessions[0].session_id;
        }
      },
      error: (err) => console.error(err),
    });
  }

  load(): void {
    this.message = '';
    this.isLoading = true;

    // Ưu tiên load theo session để có môn + giờ + vắng
    const sessionId = this.selectedSessionId ?? undefined;
    this.attendanceService.getReport(this.date, undefined, sessionId).subscribe({
      next: (rows) => {
        this.data = rows || [];
        if (!this.data.length) this.message = 'Không có dữ liệu điểm danh.';
        this.isLoading = false;
      },
      error: (err) => {
        this.message = 'Lỗi tải báo cáo. Kiểm tra backend.';
        console.error(err);
        this.isLoading = false;
      },
    });
  }

  formatSessionTime(row: AttendanceRecord): string {
    if (row.session_date && row.start_time && row.end_time) {
      return `${row.session_date} ${row.start_time}-${row.end_time}`;
    }
    if (row.attendance_date && row.attendance_time) {
      return `${row.attendance_date} ${row.attendance_time}`;
    }
    return '';
  }

  formatCheckin(row: AttendanceRecord): string {
    if (!row.checkin_time) return '';
    return row.checkin_time.replace('T', ' ').slice(0, 19);
  }

  getStatusClass(status?: string | null): string {
    const s = (status || '').toLowerCase();
    if (s.includes('đúng')) return 'status-on-time';
    if (s.includes('trễ')) return 'status-late';
    if (s.includes('vắng')) return 'status-absent';
    return 'status-unknown';
  }
}
