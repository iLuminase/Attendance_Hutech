export interface ClassModel {
  class_id: string;
  class_name?: string | null;
  subject_name?: string | null;
  lecturer_name?: string | null;
}

export interface ClassesListResponse {
  total: number;
  classes: ClassModel[];
}
