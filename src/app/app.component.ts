import { Component } from '@angular/core';
import { CertificateForm1Component } from './certificate-form1/certificate-form1.component';

@Component({
  selector: 'app-root', // The root component should have 'app-root' as the selector
  imports: [CertificateForm1Component],
  templateUrl: './app.component.html',
  styleUrls: ['./app.component.css']
})
export class AppComponent {
  title = 'my-app';
}
