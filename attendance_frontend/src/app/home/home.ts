import { CommonModule } from '@angular/common';
import { Component } from '@angular/core';
import { MatButtonModule } from '@angular/material/button';
import { MatCardModule } from '@angular/material/card';
import { MatIconModule } from '@angular/material/icon';
import { Router } from '@angular/router';

import { APP_MENU_ITEMS, AppMenuItem } from '../shared/app-menu';

@Component({
  selector: 'app-home',
  imports: [CommonModule, MatCardModule, MatButtonModule, MatIconModule],
  templateUrl: './home.html',
  styleUrl: './home.css',
})
export class Home {

  items: AppMenuItem[] = APP_MENU_ITEMS;

  constructor(private router: Router) { }

  go(route: string): void {
    this.router.navigate([route]);
  }
}
