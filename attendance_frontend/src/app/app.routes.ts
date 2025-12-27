import { Routes } from '@angular/router';
import { AddPictureForStudent } from './add-picture-for-student/add-picture-for-student';
import { ClassesList } from './classes-list/classes-list';
import { Home } from './home/home';
import { Menu } from './menu/menu';
import { Report } from './report/report';
import { Settings } from './settings/settings';
import { StudentDetail } from './student-detail/student-detail';
import { StudentsList } from './students-list/students-list';
import { TurnOnCamera } from './turn-on-camera/turn-on-camera';

export const routes: Routes = [
    { path: '', component: Home },
    { path: 'menu', component: Menu },
    { path: 'students', component: StudentsList },
    { path: 'students/:id', component: StudentDetail },
    { path: 'classes', component: ClassesList },
    { path: 'attendance', component: TurnOnCamera },
    { path: 'add-photo', component: AddPictureForStudent },
    { path: 'reports', component: Report },
    { path: 'settings', component: Settings },
    { path: '**', redirectTo: '' }
];
