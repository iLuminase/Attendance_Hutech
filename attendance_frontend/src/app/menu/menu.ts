import { CommonModule } from '@angular/common';
import { Component } from '@angular/core';
import { MatButtonModule } from '@angular/material/button';
import { MatCardModule } from '@angular/material/card';
import { MatGridListModule } from '@angular/material/grid-list';
import { MatIconModule } from '@angular/material/icon';
import { Router } from '@angular/router';

import { APP_MENU_ITEMS, AppMenuItem } from '../shared/app-menu';

@Component({
  selector: 'app-menu',
  imports: [CommonModule, MatCardModule, MatIconModule, MatButtonModule, MatGridListModule],
  templateUrl: './menu.html',
  styleUrl: './menu.css',
})
export class Menu {

  constructor(private router: Router) { }

  menuItems: AppMenuItem[] = APP_MENU_ITEMS;

  onMenuClick(route: string) {
    console.log('Điều hướng đến:', route);
    this.router.navigate([route]);
  }
}
