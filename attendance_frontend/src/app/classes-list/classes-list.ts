import { CommonModule } from '@angular/common';
import { Component, OnDestroy, OnInit } from '@angular/core';
import { MatButtonModule } from '@angular/material/button';
import { MatCardModule } from '@angular/material/card';
import { MatIconModule } from '@angular/material/icon';
import { MatProgressSpinnerModule } from '@angular/material/progress-spinner';
import { MatTableModule } from '@angular/material/table';
import { Subject, takeUntil } from 'rxjs';

import { ClassModel } from '../models/class.model';
import { ClassService } from '../services/class';

@Component({
  selector: 'app-classes-list',
  imports: [
    CommonModule,
    MatCardModule,
    MatButtonModule,
    MatIconModule,
    MatTableModule,
    MatProgressSpinnerModule,
  ],
  templateUrl: './classes-list.html',
  styleUrl: './classes-list.css',
})
export class ClassesList implements OnInit, OnDestroy {
  isLoading = false;
  message = '';

  total = 0;
  data: ClassModel[] = [];
  displayedColumns: string[] = ['class_id', 'class_name', 'subject_name', 'lecturer_name'];

  private destroy$ = new Subject<void>();

  constructor(private classService: ClassService) { }

  ngOnInit(): void {
    this.load();
  }

  ngOnDestroy(): void {
    this.destroy$.next();
    this.destroy$.complete();
  }

  load(): void {
    this.message = '';
    this.isLoading = true;

    this.classService.getClasses()
      .pipe(takeUntil(this.destroy$))
      .subscribe({
        next: (res) => {
          this.total = res?.total ?? 0;
          this.data = res?.classes || [];
          if (!this.data.length) this.message = 'Chưa có lớp học.';
          this.isLoading = false;
        },
        error: (err) => {
          console.error(err);
          this.message = 'Lỗi tải danh sách lớp. Kiểm tra backend.';
          this.isLoading = false;
        },
      });
  }
}
