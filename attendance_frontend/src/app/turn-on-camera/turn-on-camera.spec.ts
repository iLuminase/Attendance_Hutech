import { ComponentFixture, TestBed } from '@angular/core/testing';

import { TurnOnCamera } from './turn-on-camera';

describe('TurnOnCamera', () => {
  let component: TurnOnCamera;
  let fixture: ComponentFixture<TurnOnCamera>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [TurnOnCamera]
    })
    .compileComponents();

    fixture = TestBed.createComponent(TurnOnCamera);
    component = fixture.componentInstance;
    await fixture.whenStable();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
