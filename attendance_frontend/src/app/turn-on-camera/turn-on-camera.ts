import { CommonModule } from '@angular/common';
import { Component, ElementRef, OnDestroy, OnInit, ViewChild } from '@angular/core';
import { MatButtonModule } from '@angular/material/button';
import { MatCardModule } from '@angular/material/card';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatIconModule } from '@angular/material/icon';
import { MatListModule } from '@angular/material/list';
import { MatSelectModule } from '@angular/material/select';

import { AttendanceRecord } from '../models/attendance.model';
import { ClassModel } from '../models/class.model';
import { SessionModel } from '../models/session.model';
import { AttendanceService } from '../services/attendance';
import { ClassService } from '../services/class';
import { FaceBox, FaceRecognizeResponse, FaceService, RecognizedStudent } from '../services/face';
import { SessionService } from '../services/session';

@Component({
  selector: 'app-turn-on-camera',
  imports: [
    CommonModule,
    MatCardModule,
    MatButtonModule,
    MatListModule,
    MatFormFieldModule,
    MatSelectModule,
    MatIconModule,
  ],
  templateUrl: './turn-on-camera.html',
  styleUrl: './turn-on-camera.css',
})
export class TurnOnCamera implements OnInit, OnDestroy {
  @ViewChild('video', { static: false }) videoRef?: ElementRef<HTMLVideoElement>;
  @ViewChild('canvas', { static: false }) canvasRef?: ElementRef<HTMLCanvasElement>;
  @ViewChild('overlay', { static: false }) overlayRef?: ElementRef<HTMLCanvasElement>;

  isCameraOn = false;
  isRecognizing = false;
  isCheckingIn = false;
  facesCount = 0;
  recognizedCount = 0;
  message = '';

  // Panel: kết quả nhận diện gần nhất
  lastRecognized: RecognizedStudent[] = [];
  lastRecognizeAt: string | null = null;

  sessions: SessionModel[] = [];
  selectedSessionId: number | null = null;

  // Chọn lớp (tuỳ chọn) - có thể chọn nhiều lớp nếu cùng ngày và chưa kết thúc
  classes: ClassModel[] = [];
  private classNameById = new Map<string, string>();
  selectedClassIds: string[] = [];

  // Panel bên phải: danh sách SV đã điểm danh
  checkedIn: AttendanceRecord[] = [];
  private checkedInSet = new Set<string>();

  private stream: MediaStream | null = null;
  private timerId: number | null = null;
  private lastTickAt = 0;

  constructor(
    private attendanceService: AttendanceService,
    private faceService: FaceService,
    private sessionService: SessionService,
    private classService: ClassService,
  ) { }

  ngOnInit(): void {
    this.classService.getClasses().subscribe({
      next: (res) => {
        this.classes = res?.classes || [];
        this.classNameById.clear();
        for (const c of this.classes) {
          const name = (c.class_name || '').trim();
          this.classNameById.set(c.class_id, name || c.class_id);
        }
      },
      error: (err) => console.error(err),
    });

    this.sessionService.getSessions().subscribe({
      next: (rows) => {
        this.sessions = rows || [];
      },
      error: (err) => {
        console.error(err);
      },
    });
  }

  getClassName(classId?: string | null): string {
    if (!classId) return '';
    return this.classNameById.get(classId) || classId;
  }

  private isToday(dateStr: string): boolean {
    // session_date dạng YYYY-MM-DD
    const now = new Date();
    const yyyy = now.getFullYear();
    const mm = String(now.getMonth() + 1).padStart(2, '0');
    const dd = String(now.getDate()).padStart(2, '0');
    return dateStr === `${yyyy}-${mm}-${dd}`;
  }

  private isNotEnded(endTimeStr: string): boolean {
    // end_time dạng HH:MM:SS
    const parts = endTimeStr.split(':').map((x) => parseInt(x, 10));
    const hh = parts[0] || 0;
    const mi = parts[1] || 0;
    const ss = parts[2] || 0;
    const now = new Date();
    const end = new Date(now.getFullYear(), now.getMonth(), now.getDate(), hh, mi, ss);
    return end.getTime() > now.getTime();
  }

  getActiveSessions(): SessionModel[] {
    return (this.sessions || []).filter((s) => this.isToday(s.session_date) && this.isNotEnded(s.end_time));
  }

  getActiveClassIds(): string[] {
    const set = new Set<string>();
    for (const s of this.getActiveSessions()) {
      if (s.class_id) set.add(s.class_id);
    }
    return Array.from(set);
  }

  onSessionChange(): void {
    // Nếu chọn session thì khóa lớp theo session
    const s = this.sessions.find((x) => x.session_id === this.selectedSessionId);
    if (s?.class_id) {
      this.selectedClassIds = [s.class_id];
    }
  }

  onClassSelectionChange(): void {
    // Nếu chọn nhiều lớp thì bỏ chọn session (vì session_id chỉ có 1)
    if (this.selectedClassIds.length > 1) {
      this.selectedSessionId = null;
    }
  }

  async startCamera(): Promise<void> {
    try {
      this.message = '';
      this.recognizedCount = 0;
      this.lastRecognized = [];
      this.lastRecognizeAt = null;
      this.checkedIn = [];
      this.checkedInSet.clear();

      this.stream = await navigator.mediaDevices.getUserMedia({
        video: { width: 640, height: 480 },
        audio: false,
      });

      const video = this.videoRef?.nativeElement;
      if (!video) return;

      video.srcObject = this.stream;
      await video.play();
      this.isCameraOn = true;

      // Gửi frame định kỳ để phát hiện/nhận diện
      this.timerId = window.setInterval(() => this.tick(), 900);
    } catch (e: any) {
      this.message = 'Không mở được camera. Vui lòng kiểm tra quyền truy cập.';
      console.error(e);
      this.stopCamera();
    }
  }

  stopCamera(): void {
    if (this.timerId) {
      window.clearInterval(this.timerId);
      this.timerId = null;
    }
    if (this.stream) {
      this.stream.getTracks().forEach((t) => t.stop());
      this.stream = null;
    }
    this.isCameraOn = false;
    this.isRecognizing = false;
    this.isCheckingIn = false;
    this.facesCount = 0;
    this.recognizedCount = 0;
    this.clearOverlay();
  }

  private async tick(): Promise<void> {
    if (!this.isCameraOn) return;
    if (this.isRecognizing || this.isCheckingIn) return;

    // Throttle để tránh spam API
    const now = Date.now();
    if (now - this.lastTickAt < 700) return;
    this.lastTickAt = now;

    const blob = await this.captureFrame();
    if (!blob) return;

    this.isRecognizing = true;
    this.faceService.recognize(blob).subscribe({
      next: (res: FaceRecognizeResponse) => {
        this.facesCount = res.faces_count;
        this.recognizedCount = res.recognized_count ?? 0;
        this.message = res.message;
        this.lastRecognizeAt = new Date().toLocaleTimeString('vi-VN');
        this.lastRecognized = (res.recognized_students || []).filter((x): x is RecognizedStudent => !!x);
        this.drawOverlay(res);
        this.isRecognizing = false;

        if (this.recognizedCount > 0) {
          this.checkin(blob);
        }
      },
      error: (err) => {
        this.isRecognizing = false;
        this.message = 'Lỗi nhận diện. Kiểm tra backend.';
        console.error(err);
        this.recognizedCount = 0;
        this.lastRecognized = [];
        this.lastRecognizeAt = new Date().toLocaleTimeString('vi-VN');
        this.clearOverlay();
      },
    });
  }

  getStatusText(): string {
    if (!this.isCameraOn) return 'Camera đang tắt';
    if (this.isCheckingIn) return 'Đang điểm danh...';
    if (this.isRecognizing) return 'Đang nhận diện...';
    return 'Sẵn sàng';
  }

  private checkin(blob: Blob): void {
    if (this.isCheckingIn) return;
    this.isCheckingIn = true;

    const session = this.sessions.find((x) => x.session_id === this.selectedSessionId);
    const sessionId = this.selectedSessionId ?? undefined;

    const classIds = session?.class_id
      ? [session.class_id]
      : (this.selectedClassIds.length > 1 ? [...this.selectedClassIds] : undefined);

    const classId = session?.class_id
      ? session.class_id
      : (this.selectedClassIds.length === 1 ? this.selectedClassIds[0] : undefined);

    this.attendanceService.checkinByFace(blob, sessionId, classId, classIds).subscribe({
      next: (res) => {
        // Cập nhật panel bên phải: chỉ thêm mới theo student_id
        (res.attendances || []).forEach((a) => {
          if (!a?.student_id) return;
          if (this.checkedInSet.has(a.student_id)) return;
          this.checkedInSet.add(a.student_id);
          this.checkedIn = [a, ...this.checkedIn];
        });

        this.isCheckingIn = false;
      },
      error: (err) => {
        this.isCheckingIn = false;
        console.error(err);
      },
    });
  }

  private async captureFrame(): Promise<Blob | null> {
    const video = this.videoRef?.nativeElement;
    const canvas = this.canvasRef?.nativeElement;
    const overlay = this.overlayRef?.nativeElement;
    if (!video || !canvas) return null;

    const ctx = canvas.getContext('2d');
    if (!ctx) return null;

    const w = video.videoWidth || 640;
    const h = video.videoHeight || 480;
    canvas.width = w;
    canvas.height = h;
    if (overlay) {
      overlay.width = w;
      overlay.height = h;
    }

    // Vẽ frame hiện tại lên canvas
    ctx.drawImage(video, 0, 0, w, h);

    return await new Promise<Blob | null>((resolve) => {
      canvas.toBlob((b) => resolve(b), 'image/jpeg', 0.8);
    });
  }

  private drawOverlay(res: FaceRecognizeResponse): void {
    const overlay = this.overlayRef?.nativeElement;
    if (!overlay) return;
    const ctx = overlay.getContext('2d');
    if (!ctx) return;

    ctx.clearRect(0, 0, overlay.width, overlay.height);

    const faces: FaceBox[] = res.faces || [];
    const recognized = res.recognized_students || [];

    for (let i = 0; i < faces.length; i++) {
      const f = faces[i];
      const info = recognized[i];

      // Border
      ctx.lineWidth = 3;
      ctx.strokeStyle = info ? 'lime' : 'yellow';
      ctx.strokeRect(f.x, f.y, f.w, f.h);

      // Label
      const label = info ? `${info.student_id} - ${info.name}` : 'Unknown';
      ctx.font = '16px Arial';
      const textW = ctx.measureText(label).width;
      const pad = 6;
      const x = Math.max(0, f.x);
      const y = Math.max(18, f.y - 6);

      ctx.fillStyle = 'rgba(0,0,0,0.6)';
      ctx.fillRect(x, y - 18, textW + pad * 2, 22);
      ctx.fillStyle = 'white';
      ctx.fillText(label, x + pad, y - 2);
    }
  }

  private clearOverlay(): void {
    const overlay = this.overlayRef?.nativeElement;
    if (!overlay) return;
    const ctx = overlay.getContext('2d');
    if (!ctx) return;
    ctx.clearRect(0, 0, overlay.width, overlay.height);
  }

  formatAttendanceTime(row: AttendanceRecord): string {
    // Ưu tiên format kiểu date + time
    if (row.attendance_date && row.attendance_time) {
      return `${row.attendance_date} ${row.attendance_time}`;
    }
    // checkin_time thường là ISO string
    if (row.checkin_time) {
      // Cắt ngắn cho dễ nhìn
      return row.checkin_time.replace('T', ' ').slice(0, 19);
    }
    return '';
  }

  ngOnDestroy(): void {
    this.stopCamera();
  }
}
