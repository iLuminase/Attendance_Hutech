import { CommonModule } from '@angular/common';
import { Component } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { MatButtonModule } from '@angular/material/button';
import { MatCardModule } from '@angular/material/card';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatIconModule } from '@angular/material/icon';
import { MatInputModule } from '@angular/material/input';
import { Router } from '@angular/router';

import { getBackendBaseUrl, setBackendBaseUrl } from '../services/api-config';

@Component({
  selector: 'app-settings',
  imports: [
    CommonModule,
    FormsModule,
    MatCardModule,
    MatButtonModule,
    MatIconModule,
    MatFormFieldModule,
    MatInputModule,
  ],
  templateUrl: './settings.html',
  styleUrl: './settings.css',
})
export class Settings {

  backendBaseUrl = getBackendBaseUrl();
  apiStudents = '';
  apiClasses = '';
  apiSessions = '';
  apiFace = '';
  apiAttendance = '';
  savedMessage = '';

  constructor(private router: Router) { }

  ngOnInit(): void {
    this.refreshApiUrls();
  }

  saveBackendUrl(): void {
    setBackendBaseUrl(this.backendBaseUrl);
    this.backendBaseUrl = getBackendBaseUrl();
    this.refreshApiUrls();
    this.savedMessage = 'Đã lưu cấu hình backend (lưu trên trình duyệt).';
  }

  private refreshApiUrls(): void {
    const base = this.backendBaseUrl;
    this.apiStudents = `${base}/api/students`;
    this.apiClasses = `${base}/api/classes`;
    this.apiSessions = `${base}/api/sessions`;
    this.apiFace = `${base}/api/face`;
    this.apiAttendance = `${base}/api/attendance`;
  }

  go(route: string): void {
    this.router.navigate([route]);
  }

}
