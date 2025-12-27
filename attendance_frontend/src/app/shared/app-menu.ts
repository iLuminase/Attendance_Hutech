export interface AppMenuItem {
  title: string;
  description: string;
  icon: string;
  route: string;
}

export const APP_MENU_ITEMS: AppMenuItem[] = [
  {
    title: 'Điểm danh bằng khuôn mặt',
    description: 'Bật camera, nhận diện và ghi nhận điểm danh',
    icon: 'camera_alt',
    route: '/attendance',
  },
  {
    title: 'Đăng ký ảnh khuôn mặt',
    description: 'Chọn sinh viên và tải ảnh để huấn luyện/đăng ký',
    icon: 'add_a_photo',
    route: '/add-photo',
  },
  {
    title: 'Danh sách sinh viên',
    description: 'Xem và quản lý thông tin sinh viên',
    icon: 'groups',
    route: '/students',
  },
  {
    title: 'Danh sách lớp học',
    description: 'Xem thông tin lớp học (cơ bản)',
    icon: 'school',
    route: '/classes',
  },
  {
    title: 'Báo cáo điểm danh',
    description: 'Tra cứu kết quả điểm danh theo ngày',
    icon: 'assessment',
    route: '/reports',
  },
  {
    title: 'Cài đặt',
    description: 'Thông tin cấu hình demo',
    icon: 'settings',
    route: '/settings',
  },
];
