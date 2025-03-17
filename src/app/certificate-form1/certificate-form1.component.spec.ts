import { ComponentFixture, TestBed } from '@angular/core/testing';

import { CertificateForm1Component } from './certificate-form1.component';

describe('CertificateForm1Component', () => {
  let component: CertificateForm1Component;
  let fixture: ComponentFixture<CertificateForm1Component>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [CertificateForm1Component]
    })
    .compileComponents();

    fixture = TestBed.createComponent(CertificateForm1Component);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
