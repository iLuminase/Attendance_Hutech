import { CommonModule } from '@angular/common';
import { Component, OnDestroy, OnInit } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { MatButtonModule } from '@angular/material/button';
import { MatCardModule } from '@angular/material/card';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatIconModule } from '@angular/material/icon';
import { MatProgressSpinnerModule } from '@angular/material/progress-spinner';
import { MatSelectModule } from '@angular/material/select';
import { MatSnackBar, MatSnackBarModule } from '@angular/material/snack-bar';
import { Subject, takeUntil } from 'rxjs';

import { ClassModel } from '../models/class.model';
import { Student as StudentModel } from '../models/student.model';
import { ClassService } from '../services/class';
import { StudentService } from '../services/student';

@Component({
  selector: 'app-add-picture-for-student',
  imports: [
    CommonModule,
    FormsModule,
    MatCardModule,
    MatFormFieldModule,
    MatSelectModule,
    MatButtonModule,
    MatIconModule,
    MatProgressSpinnerModule,
    MatSnackBarModule,
  ],
  templateUrl: './add-picture-for-student.html',
  styleUrl: './add-picture-for-student.css',
})
export class AddPictureForStudent implements OnInit, OnDestroy {
  students: StudentModel[] = [];
  selectedStudentId: string | null = null;

  classes: ClassModel[] = [];
  private classNameById = new Map<string, string>();

  selectedFile: File | null = null;
  previewUrl: string | null = null;

  isLoadingStudents = false;
  isUploading = false;
  statusMessage = '';

  hasFaceImage: boolean | null = null;
  hasFaceEncoding: boolean | null = null;

  private destroy$ = new Subject<void>();

  constructor(
    private studentService: StudentService,
    private classService: ClassService,
    private snackBar: MatSnackBar,
  ) { }

  ngOnInit(): void {
    this.loadClasses();
    this.loadStudents();
  }
  private loadClasses(): void {
    this.classService.getClasses()
      .pipe(takeUntil(this.destroy$))
      .subscribe({
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
  }

  getClassName(classId?: string | null): string {
    if (!classId) return '';
    return this.classNameById.get(classId) || classId;
  }


  ngOnDestroy(): void {
    this.destroy$.next();
    this.destroy$.complete();
    this.revokePreview();
  }

  loadStudents(): void {
    this.isLoadingStudents = true;
    this.studentService.getStudents()
      .pipe(takeUntil(this.destroy$))
      .subscribe({
        next: (rows) => {
          this.students = rows || [];
          this.isLoadingStudents = false;
        },
        error: (err) => {
          console.error(err);
          this.isLoadingStudents = false;
          this.openError('Không tải được danh sách sinh viên');
        }
      });
  }

  onStudentChange(): void {
    this.statusMessage = '';
    this.hasFaceImage = null;
    this.hasFaceEncoding = null;
    if (!this.selectedStudentId) return;

    this.studentService.hasFaceImage(this.selectedStudentId)
      .pipe(takeUntil(this.destroy$))
      .subscribe({
        next: (res) => {
          this.hasFaceImage = !!res?.has_face_image;
          this.hasFaceEncoding = !!res?.has_face_encoding;
        },
        error: (err) => {
          console.error(err);
        }
      });
  }

  onFileSelected(event: Event): void {
    const input = event.target as HTMLInputElement;
    const file = input.files?.[0] || null;
    this.setSelectedFile(file);
  }

  private setSelectedFile(file: File | null): void {
    this.selectedFile = file;
    this.statusMessage = '';

    this.revokePreview();
    if (!file) {
      this.previewUrl = null;
      return;
    }
    this.previewUrl = URL.createObjectURL(file);
  }

  private revokePreview(): void {
    if (this.previewUrl) {
      URL.revokeObjectURL(this.previewUrl);
    }
    this.previewUrl = null;
  }

  upload(): void {
    this.statusMessage = '';
    if (!this.selectedStudentId) {
      this.openError('Vui lòng chọn sinh viên');
      return;
    }
    if (!this.selectedFile) {
      this.openError('Vui lòng chọn ảnh khuôn mặt');
      return;
    }

    this.isUploading = true;
    this.studentService.uploadFaceImage(this.selectedStudentId, this.selectedFile)
      .pipe(takeUntil(this.destroy$))
      .subscribe({
        next: (res) => {
          this.isUploading = false;
          this.statusMessage = res?.message || 'Đăng ký ảnh khuôn mặt thành công';
          this.openSuccess(this.statusMessage);
          this.onStudentChange();
        },
        error: (err) => {
          this.isUploading = false;
          console.error(err);
          const detail = err?.error?.detail || err?.message || '';
          this.statusMessage = detail ? `Không đăng ký được ảnh: ${detail}` : 'Không đăng ký được ảnh';
          this.openError(this.statusMessage);
        }
      });
  }

  clear(): void {
    this.setSelectedFile(null);
    this.statusMessage = '';
  }

  private openSuccess(message: string): void {
    this.snackBar.open(message, 'Đóng', { duration: 2500, panelClass: ['success-snackbar'] });
  }

  private openError(message: string): void {
    this.snackBar.open(message, 'Đóng', { duration: 4000, panelClass: ['error-snackbar'] });
  }
}
