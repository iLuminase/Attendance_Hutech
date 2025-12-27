import { ComponentFixture, TestBed } from '@angular/core/testing';

import { AddPictureForStudent } from './add-picture-for-student';

describe('AddPictureForStudent', () => {
  let component: AddPictureForStudent;
  let fixture: ComponentFixture<AddPictureForStudent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [AddPictureForStudent]
    })
    .compileComponents();

    fixture = TestBed.createComponent(AddPictureForStudent);
    component = fixture.componentInstance;
    await fixture.whenStable();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
