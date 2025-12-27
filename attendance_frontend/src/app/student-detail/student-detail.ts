import { CommonModule } from '@angular/common';
import { Component, OnDestroy, OnInit } from '@angular/core';
import { FormBuilder, FormGroup, ReactiveFormsModule, Validators } from '@angular/forms';
import { MatButtonModule } from '@angular/material/button';
import { MatCardModule } from '@angular/material/card';
import { MatChipsModule } from '@angular/material/chips';
import { MatDividerModule } from '@angular/material/divider';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatIconModule } from '@angular/material/icon';
import { MatInputModule } from '@angular/material/input';
import { MatProgressSpinnerModule } from '@angular/material/progress-spinner';
import { MatSelectModule } from '@angular/material/select';
import { MatSnackBar, MatSnackBarModule } from '@angular/material/snack-bar';
import { MatToolbarModule } from '@angular/material/toolbar';
import { ActivatedRoute, Router } from '@angular/router';
import { Subject } from 'rxjs';
import { takeUntil } from 'rxjs/operators';

import { ClassModel } from '../models/class.model';
import { Student as StudentModel, UpdateStudentDto } from '../models/student.model';
import { ClassService } from '../services/class';
import { StudentService } from '../services/student';

@Component({
  selector: 'app-student-detail',
  imports: [
    CommonModule, ReactiveFormsModule,
    MatButtonModule, MatCardModule, MatFormFieldModule, MatIconModule,
    MatInputModule, MatProgressSpinnerModule, MatSnackBarModule,
    MatToolbarModule, MatChipsModule, MatDividerModule, MatSelectModule
  ],
  templateUrl: './student-detail.html',
  styleUrl: './student-detail.css'
})
export class StudentDetail implements OnInit, OnDestroy {
  student: StudentModel | null = null;
  studentForm: FormGroup;
  isLoading = false;
  isEditing = false;
  isSaving = false;
  studentId: string = '';
  hasUnsavedChanges = false;

  classes: ClassModel[] = [];
  private classNameById = new Map<string, string>();

  private destroy$ = new Subject<void>();

  constructor(
    private route: ActivatedRoute,
    private router: Router,
    private studentService: StudentService,
    private classService: ClassService,
    private fb: FormBuilder,
    private snackBar: MatSnackBar
  ) {
    this.studentForm = this.createForm();
    this.setupFormChangeDetection();
  }

  ngOnInit() {
    this.loadClasses();
    this.route.params.pipe(takeUntil(this.destroy$)).subscribe(params => {
      this.studentId = params['id'];
      if (this.studentId) {
        this.loadStudent();
      }
    });
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

  ngOnDestroy() {
    this.destroy$.next();
    this.destroy$.complete();
  }

  private createForm(): FormGroup {
    return this.fb.group({
      student_id: ['', Validators.required],
      name: ['', Validators.required],
      email: ['', [Validators.required, Validators.email]],
      phone: [''],
      class_id: ['', [Validators.required]]
    });
  }

  private setupFormChangeDetection() {
    this.studentForm.valueChanges
      .pipe(takeUntil(this.destroy$))
      .subscribe(() => {
        if (this.student && !this.isSaving) {
          this.hasUnsavedChanges = this.checkForChanges();
        }
      });
  }

  private checkForChanges(): boolean {
    if (!this.student) return false;

    const formValue = this.studentForm.value;
    return (
      formValue.student_id !== this.student.student_id ||
      formValue.name !== this.student.name ||
      formValue.email !== this.student.email ||
      formValue.phone !== this.student.phone ||
      formValue.class_id?.toString() !== this.student.class_id?.toString()
    );
  }

  loadStudent() {
    this.isLoading = true;
    this.studentService.getStudent(this.studentId)
      .pipe(takeUntil(this.destroy$))
      .subscribe({
        next: (student) => {
          this.student = student;
          this.studentForm.patchValue({
            student_id: student.student_id,
            name: student.name,
            email: student.email,
            phone: student.phone || '',
            class_id: student.class_id
          });
          this.hasUnsavedChanges = false;
          this.isLoading = false;
        },
        error: (error) => {
          console.error('Error loading student:', error);
          this.showError('Không thể tải thông tin sinh viên');
          this.isLoading = false;
        }
      });
  }

  toggleEdit() {
    if (this.isEditing && this.hasUnsavedChanges) {
      if (confirm('Bạn có chắc muốn hủy các thay đổi chưa lưu?')) {
        this.cancelEdit();
      }
    } else {
      this.isEditing = !this.isEditing;
      if (!this.isEditing) {
        this.cancelEdit();
      }
    }
  }

  cancelEdit() {
    this.isEditing = false;
    if (this.student) {
      this.studentForm.patchValue({
        student_id: this.student.student_id,
        name: this.student.name,
        email: this.student.email,
        phone: this.student.phone || '',
        class_id: this.student.class_id
      });
    }
    this.hasUnsavedChanges = false;
  }

  saveChanges() {
    if (this.studentForm.valid && this.student) {
      this.isSaving = true;
      const formValue = this.studentForm.value;

      const updateData: UpdateStudentDto = {
        student_id: formValue.student_id,
        name: formValue.name,
        email: formValue.email,
        phone: formValue.phone,
        class_id: String(formValue.class_id)
      };

      this.studentService.updateStudent(this.studentId, updateData)
        .pipe(takeUntil(this.destroy$))
        .subscribe({
          next: (updatedStudent) => {
            this.student = updatedStudent;
            this.isEditing = false;
            this.hasUnsavedChanges = false;
            this.isSaving = false;
            this.showSuccess('Cập nhật thông tin thành công!');
          },
          error: (error) => {
            console.error('Error updating student:', error);
            this.showError('Lỗi khi cập nhật thông tin');
            this.isSaving = false;
          }
        });
    }
  }

  uploadImage() {
    const input = document.createElement('input');
    input.type = 'file';
    input.accept = 'image/*';
    input.onchange = (event: any) => {
      const file = event.target.files[0];
      if (file && this.student) {
        // TODO: Implement image upload when needed
        console.log('Image upload selected:', file.name);
        this.showSuccess(`Ảnh ${file.name} đã chọn, chức năng upload sẽ được thêm sau`);
      }
    };
    input.click();
  }

  goBack() {
    if (this.hasUnsavedChanges) {
      if (confirm('Bạn có chắc muốn rời khỏi trang này? Các thay đổi chưa lưu sẽ bị mất.')) {
        this.router.navigate(['/students']);
      }
    } else {
      this.router.navigate(['/students']);
    }
  }

  private showSuccess(message: string) {
    this.snackBar.open(message, 'Đóng', {
      duration: 3000,
      panelClass: ['success-snackbar']
    });
  }

  private showError(message: string) {
    this.snackBar.open(message, 'Đóng', {
      duration: 5000,
      panelClass: ['error-snackbar']
    });
  }
}
