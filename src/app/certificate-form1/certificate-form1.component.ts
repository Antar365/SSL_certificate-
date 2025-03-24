import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';
import { HttpClient } from '@angular/common/http';
import { FormsModule } from '@angular/forms';
import { ReactiveFormsModule, FormGroup, FormBuilder, Validators } from '@angular/forms';

@Component({
  selector: 'app-certificate-form1',
  standalone: true,
  imports: [CommonModule, FormsModule, ReactiveFormsModule],
  templateUrl: './certificate-form1.component.html',
  styleUrls: ['./certificate-form1.component.css']
})
export class CertificateForm1Component {
  certificateForm: FormGroup;
  downloadUrl: string | null = null;
  isLoading: boolean = false;
  certificates: any[] = [];
  showTable: boolean = false;
  buttonText: string = 'View All Certificates';
  caInfo: string = 'Loading...'; // Holds CA details

  private API_URL = 'http://127.0.0.1:8000';

  constructor(private fb: FormBuilder, private http: HttpClient) {
    this.certificateForm = this.fb.group({
      common_name: ['', Validators.required],
      subject_alt_name: ['', Validators.required],
      organization: ['', Validators.required],
      organization_unit: ['', Validators.required],
      locality: ['', Validators.required],
      state: ['', Validators.required],
      country: ['', [Validators.required, Validators.pattern(/^[A-Z]{2}$/)]],
      validity_days: ['', Validators.required]
    });

    // Fetch CA details when component loads
    this.getCAInfo();
  }

  generateCertificate() {
    if (!this.certificateForm.valid) {
      alert('Form is not valid. Please fill all required fields.');
      return;
    }
  
    const formData = {
      ...this.certificateForm.value,
      validity_days: Number(this.certificateForm.value.validity_days)
    };
  
    console.log('Sending request with data:', formData);
  
    this.isLoading = true;
  
    this.http.post<{ message: string; download_url: string; expiry_date: string }>(
      `${this.API_URL}/generate-certificate`,
      formData,
      { headers: { 'Content-Type': 'application/json' } }
    ).subscribe(
      response => {
        console.log('Response received:', response);
        alert(`Certificate generated successfully!\nExpiry Date: ${response.expiry_date}`);
        this.isLoading = false;
  
        if (response.download_url) {
          this.downloadUrl = new URL(response.download_url, this.API_URL).href;
          console.log('Download URL:', this.downloadUrl);
        } else {
          console.error('Download URL not returned by API');
          alert('Download URL not received');
        }
      },
      error => {
        console.error('Error generating certificate:', error);
        let errorMessage = error.error?.detail || `Failed to generate certificate. Server Response: ${error.status} - ${error.statusText}`;
        alert(errorMessage);
        this.isLoading = false;
      }
    );
  }

  viewCertificates() {
    if (!this.showTable) {
      this.http.get<{ certificates: any[] }>(`${this.API_URL}/certificates`)
        .subscribe(
          response => {
            console.log("Certificates Data:", response.certificates);
            if (response.certificates?.length) {
              this.certificates = response.certificates.map(cert => ({
                _id: cert._id,  
                common_name: cert.common_name,
                organization: cert.organization,
                expiry_date: cert.expiry_date || "Not Available",
                download_link: `${this.API_URL}/download-certificate/${cert._id}`
              }));
            } else {
              alert("No certificates found.");
            }
          },
          error => {
            console.error("Error fetching certificates:", error);
            alert("Failed to fetch certificates");
          }
        );
    }
    
    this.showTable = !this.showTable; 
    this.buttonText = this.showTable ? 'Show Original' : 'View All Certificates'; 
  }

  // New method to fetch CA details
getCAInfo() {
  this.http.get<{ ca_name: string }>(`${this.API_URL}/ca-name`)
    .subscribe(
      response => {
        console.log("CA Info:", response);
        this.caInfo = response.ca_name;
      },
      error => {
        console.error("Failed to fetch CA info:", error);
        this.caInfo = "Error fetching CA info";
      }
    );
}

// New method to download CA certificate
downloadCA() {
  const downloadUrl = `${this.API_URL}/download-ca`;
  const link = document.createElement("a");
  link.href = downloadUrl;
  link.download = "rootCA.crt"; // Suggested filename
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
}
}
