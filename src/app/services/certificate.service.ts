import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';

@Injectable({
  providedIn: 'root',
})
export class CertificateService {
  private apiUrl = 'http://localhost:8000'; // Your backend API URL

  constructor(private http: HttpClient) {}

  generateCertificate(data: any): Observable<any> {
    return this.http.post(`${this.apiUrl}/generate-certificate/`, data);
  }

  downloadCertificate(certId: string): Observable<Blob> {
    return this.http.get(`${this.apiUrl}/download-certificate/${certId}`, {
      responseType: 'blob',
    });
  }
}
