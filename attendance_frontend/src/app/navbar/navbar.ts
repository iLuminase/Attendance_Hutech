import { CommonModule } from '@angular/common';
import { Component, OnDestroy } from '@angular/core';
import { MatButtonModule } from '@angular/material/button';
import { MatIconModule } from '@angular/material/icon';
import { MatMenuModule } from '@angular/material/menu';
import { MatToolbarModule } from '@angular/material/toolbar';
import { Router } from '@angular/router';
import { interval, map, Observable, Subject, takeUntil } from 'rxjs';

@Component({
  selector: 'app-navbar',
  imports: [CommonModule, MatToolbarModule, MatIconModule, MatButtonModule, MatMenuModule],
  templateUrl: './navbar.html',
  styleUrl: './navbar.css'
})
export class Navbar implements OnDestroy {
  // 🔥 Observable stream cho async pipe - Tự động trigger change detection
  currentTime$: Observable<string>;
  private destroy$ = new Subject<void>();

  constructor(private router: Router) {
    this.currentTime$ = this.initializeRxJSClock();
  }

  // 🔥 RxJS Observable Clock - Tự động cập nhật mỗi giây
  private initializeRxJSClock(): Observable<string> {
    return interval(1000).pipe(
      map(() => {
        const now = new Date();
        return now.toLocaleString('vi-VN', {
          weekday: 'long',
          year: 'numeric',
          month: 'long',
          day: 'numeric',
          hour: '2-digit',
          minute: '2-digit',
          second: '2-digit'
        });
      }),
      takeUntil(this.destroy$)
    );
  }

  ngOnDestroy() {
    this.destroy$.next();
    this.destroy$.complete();
  }



  navigateToHome() {
    this.router.navigate(['']);
  }

  openProfile() {
    console.log('Mở profile người dùng');
  }

  logout() {
    console.log('Đăng xuất');
  }
}
