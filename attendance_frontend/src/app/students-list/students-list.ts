import { CommonModule } from '@angular/common';
import { Component, OnDestroy, OnInit, ViewChild } from '@angular/core';
import { FormBuilder, FormGroup, FormsModule, ReactiveFormsModule, Validators } from '@angular/forms';
import { MatButtonModule } from '@angular/material/button';
import { MatCardModule } from '@angular/material/card';
import { MatCheckboxModule } from '@angular/material/checkbox';
import { MatChipsModule } from '@angular/material/chips';
import { MatNativeDateModule } from '@angular/material/core';
import { MatDatepickerModule } from '@angular/material/datepicker';
import { MatDialog, MatDialogModule, MatDialogRef } from '@angular/material/dialog';
import { MatDividerModule } from '@angular/material/divider';
import { MatIconModule } from '@angular/material/icon';
import { MatInputModule } from '@angular/material/input';
import { MatMenuModule } from '@angular/material/menu';
import { MatPaginator, MatPaginatorModule } from '@angular/material/paginator';
import { MatProgressSpinnerModule } from '@angular/material/progress-spinner';
import { MatSelectModule } from '@angular/material/select';
import { MatSnackBar, MatSnackBarModule } from '@angular/material/snack-bar';
import { MatSort, MatSortModule } from '@angular/material/sort';
import { MatTableDataSource, MatTableModule } from '@angular/material/table';
import { MatToolbarModule } from '@angular/material/toolbar';
import { Router } from '@angular/router';
import { debounceTime, distinctUntilChanged, Subject, takeUntil } from 'rxjs';

import { ClassModel } from '../models/class.model';
import { CreateStudentDto, StudentFilter, Student as StudentModel, UpdateStudentDto } from '../models/student.model';
import { ClassService } from '../services/class';
import { StudentService } from '../services/student';
// Import thêm để sử dụng trong dialog
import { Inject } from '@angular/core';
import { MAT_DIALOG_DATA } from '@angular/material/dialog';
import { MatFormFieldModule } from '@angular/material/form-field';


@Component({
  selector: 'app-students-list',
  imports: [
    CommonModule, FormsModule, ReactiveFormsModule,
    MatTableModule, MatPaginatorModule, MatSortModule,
    MatInputModule, MatButtonModule, MatIconModule,
    MatDialogModule, MatSelectModule, MatDatepickerModule, MatNativeDateModule,
    MatCardModule, MatChipsModule, MatMenuModule,
    MatProgressSpinnerModule, MatSnackBarModule, MatToolbarModule,
    MatCheckboxModule, MatFormFieldModule, MatDividerModule
  ],
  templateUrl: './students-list.html',
  styleUrl: './students-list.css',
})
export class StudentsList implements OnInit, OnDestroy {
  // 📊 Data và State
  displayedColumns: string[] = [
    'avatar', 'student_id', 'name', 'email', 'phone', 'class_id', 'actions'
  ];
  dataSource = new MatTableDataSource<StudentModel>([]);
  filteredStudents: StudentModel[] = [];
  allStudents: StudentModel[] = [];

  // 🔍 Filter và Search
  searchForm!: FormGroup;
  currentFilter: StudentFilter = {
    search: '',
    class_id: undefined
  };

  classes: ClassModel[] = [];
  private classNameById = new Map<string, string>();

  // 🔄 Loading states
  isLoading = false;
  isCreating = false;
  isUpdating = false;
  isDeleting = false;

  // 📄 Pagination
  totalStudents = 0;
  pageSize = 10;
  pageSizeOptions = [5, 10, 25, 50];
  currentPage = 0;

  // 🎯 ViewChild references
  @ViewChild(MatPaginator) paginator!: MatPaginator;
  @ViewChild(MatSort) sort!: MatSort;

  private destroy$ = new Subject<void>();

  constructor(
    private studentService: StudentService,
    private classService: ClassService,
    private fb: FormBuilder,
    private dialog: MatDialog,
    private snackBar: MatSnackBar,
    private router: Router
  ) {
    this.initializeSearchForm();
  }

  ngOnInit() {
    this.setupSearchSubscription();
    this.loadClasses();
    this.loadStudents();
  }

  ngOnDestroy() {
    this.destroy$.next();
    this.destroy$.complete();
  }

  // 🔧 Initialize search form
  private initializeSearchForm() {
    this.searchForm = this.fb.group({
      search: [''],
      class_id: ['']
    });
  }

  // 🔍 Setup search subscription
  private setupSearchSubscription() {
    this.searchForm.get('search')?.valueChanges
      .pipe(
        debounceTime(300),
        distinctUntilChanged(),
        takeUntil(this.destroy$)
      )
      .subscribe(searchTerm => {
        this.currentFilter.search = searchTerm;
        this.applyFilter();
      });

    this.searchForm.get('class_id')?.valueChanges
      .pipe(takeUntil(this.destroy$))
      .subscribe(classId => {
        this.currentFilter.class_id = classId ? String(classId) : undefined;
        this.applyFilter();
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

  // 📋 Load students from API
  loadStudents() {
    this.isLoading = true;

    this.studentService.getStudents()
      .pipe(takeUntil(this.destroy$))
      .subscribe({
        next: (students) => {
          console.log('Loaded students data:', students);
          console.log('Students with face encoding:', students.filter(s => s.face_encoding));

          this.allStudents = students;
          this.filteredStudents = students;
          this.totalStudents = students.length;
          this.applyFilter();
          this.isLoading = false;
        },
        error: (error) => {
          this.showError('Lỗi khi tải danh sách sinh viên: ' + (error.error?.detail || error.message));
          this.isLoading = false;
        }
      });
  }

  // 🔍 Apply filter to students list
  private applyFilter() {
    let filtered = [...this.allStudents];

    // Filter by search term (name, student_id, email)
    if (this.currentFilter.search) {
      const searchTerm = this.currentFilter.search.toLowerCase();
      filtered = filtered.filter(student =>
        student.name.toLowerCase().includes(searchTerm) ||
        student.student_id.toLowerCase().includes(searchTerm) ||
        student.email.toLowerCase().includes(searchTerm)
      );
    }

    // Filter by class_id
    if (this.currentFilter.class_id) {
      filtered = filtered.filter(student =>
        student.class_id === this.currentFilter.class_id
      );
    }

    this.filteredStudents = filtered;
    this.dataSource.data = filtered;
  }

  // � Handle filter change
  onFilterChange(filterType: string, value: any) {
    if (filterType === 'class_id') {
      this.currentFilter.class_id = value ? String(value) : undefined;
    } else {
      (this.currentFilter as any)[filterType] = value;
    }
    this.applyFilter();
  }
  // 📄 Handle pagination
  onPageChange(event: any) {
    this.currentPage = event.pageIndex;
    this.pageSize = event.pageSize;
  }
  // ➕ Open create student dialog
  openCreateDialog() {
    const dialogRef = this.dialog.open(StudentFormDialog, {
      width: '800px',
      data: { isEdit: false, classes: this.classes }
    });

    dialogRef.afterClosed().subscribe(result => {
      if (result) {
        this.createStudent(result);
      }
    });
  }

  // ✏️ Open edit student dialog
  openEditDialog(student: StudentModel) {
    const dialogRef = this.dialog.open(StudentFormDialog, {
      width: '800px',
      data: { isEdit: true, student: { ...student }, classes: this.classes }
    });

    dialogRef.afterClosed().subscribe(result => {
      if (result) {
        this.updateStudent({ ...result, student_id: student.student_id });
      }
    });
  }

  // ➕ Create student
  private createStudent(studentData: CreateStudentDto) {
    this.isCreating = true;

    this.studentService.createStudent(studentData)
      .pipe(takeUntil(this.destroy$))
      .subscribe({
        next: (response) => {
          if (response) {
            this.showSuccess('Thêm sinh viên thành công');
            this.loadStudents();
          }
          this.isCreating = false;
        },
        error: (error) => {
          this.showError('Lỗi khi thêm sinh viên');
          this.isCreating = false;
        }
      });
  }

  // ✏️ Update student
  private updateStudent(studentData: UpdateStudentDto) {
    this.isUpdating = true;

    this.studentService.updateStudent(studentData.student_id, studentData as CreateStudentDto)
      .pipe(takeUntil(this.destroy$))
      .subscribe({
        next: (response) => {
          if (response) {
            this.showSuccess('Cập nhật sinh viên thành công');
            this.loadStudents();
          }
          this.isUpdating = false;
        },
        error: (error) => {
          this.showError('Lỗi khi cập nhật sinh viên');
          this.isUpdating = false;
        }
      });
  }

  // 🗑️ Delete student
  deleteStudent(student: StudentModel) {
    if (confirm(`Bạn có chắc muốn xóa sinh viên "${student.name}"?`)) {
      this.isDeleting = true;

      this.studentService.deleteStudent(student.student_id)
        .pipe(takeUntil(this.destroy$))
        .subscribe({
          next: (response) => {
            if (response) {
              this.showSuccess('Xóa sinh viên thành công');
              this.loadStudents();
            }
            this.isDeleting = false;
          },
          error: (error) => {
            this.showError('Lỗi khi xóa sinh viên');
            this.isDeleting = false;
          }
        });
    }
  }

  // 📤 Export students
  exportStudents() {
    this.showError('Chức năng xuất file đang được phát triển');
  }

  // 🐛 Debug API data
  testApiData() {
    console.log('=== API DEBUG TEST ===');
    this.studentService.getStudents()
      .pipe(takeUntil(this.destroy$))
      .subscribe({
        next: (students) => {
          console.log('Raw API Response:', students);
          console.log('Total students:', students.length);
          this.showSuccess(`Debug complete - Found ${students.length} students`);
        },
        error: (error) => {
          console.error('API Error:', error);
          this.showError('API Error - check console');
        }
      });
  }



  // 🎨 Get status color
  getStatusColor(status: string): string {
    switch (status) {
      case 'Active': return 'primary';
      case 'Graduated': return 'accent';
      case 'Inactive': return 'warn';
      case 'Suspended': return 'warn';
      default: return '';
    }
  }

  // 📢 Show success message
  private showSuccess(message: string) {
    this.snackBar.open(message, 'Đóng', {
      duration: 3000,
      panelClass: ['success-snackbar']
    });
  }

  // ❌ Show error message
  private showError(message: string) {
    this.snackBar.open(message, 'Đóng', {
      duration: 5000,
      panelClass: ['error-snackbar']
    });
  }

  // 👁️ Navigate to student detail
  viewStudentDetail(student: StudentModel) {
    this.router.navigate(['/students', student.student_id]);
  }
















}

// 📝 Student Form Dialog Component
@Component({
  selector: 'student-form-dialog',
  templateUrl: './student-form-dialog.html',
  imports: [
    CommonModule, ReactiveFormsModule,
    MatDialogModule, MatFormFieldModule, MatInputModule,
    MatButtonModule, MatIconModule, MatSelectModule
  ]
})
export class StudentFormDialog {
  studentForm: FormGroup;
  isSubmitting = false;

  constructor(
    public dialogRef: MatDialogRef<StudentFormDialog>,
    @Inject(MAT_DIALOG_DATA) public data: any,
    private fb: FormBuilder
  ) {
    this.studentForm = this.createForm();

    if (data.isEdit && data.student) {
      this.studentForm.patchValue(data.student);
    }
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

  onSubmit() {
    if (this.studentForm.valid) {
      this.isSubmitting = true;
      const formValue = this.studentForm.value;
      this.dialogRef.close(formValue);
    }
  }

  onCancel() {
    this.dialogRef.close();
  }
}

