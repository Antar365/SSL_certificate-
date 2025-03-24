import subprocess
import os
import traceback
import uuid
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from pymongo import MongoClient
from fastapi.responses import FileResponse
from bson import ObjectId


# Initialize FastAPI
app = FastAPI()

# Enable CORS (Allow frontend to call backend)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:4200"],  # Allow all origins, change to frontend URL for security
    allow_credentials=True,
    allow_methods=["*"],  # Allow all HTTP methods
    allow_headers=["*"],  # Allow all headers
)

# MongoDB setup (Ensure you configure your MongoDB connection)
client = MongoClient("mongodb://admin:root@localhost:27017/admin")

db = client["certificate_db"]
cert_collection = db["certificates"]

# Directory to store generated files
CERTS_DIR = "generated_certs"
os.makedirs(CERTS_DIR, exist_ok=True)

# Root CA files
ROOT_CA_KEY = os.path.join(CERTS_DIR, "rootCA.key")
ROOT_CA_CERT = os.path.join(CERTS_DIR, "rootCA.crt")
ROOT_CA_SERIAL = os.path.join(CERTS_DIR, "rootCA.srl")

# Ensure Root CA exists
if not os.path.exists(ROOT_CA_KEY) or not os.path.exists(ROOT_CA_CERT):
    raise RuntimeError("Root CA key and certificate must be generated first!")

# Request Model
class CertRequest(BaseModel):
    common_name: str
    organization: str
    organization_unit: str
    locality: str
    state: str
    country: str
    subject_alt_name: str
    validity_days: int

import traceback

from datetime import datetime, timedelta

@app.post("/generate-certificate")
def generate_certificate(cert_data: CertRequest):
    try:
        unique_id = str(uuid.uuid4())
        private_key_file = os.path.join(CERTS_DIR, f"{unique_id}_private.key")
        csr_file = os.path.join(CERTS_DIR, f"{unique_id}.csr")
        cert_file = os.path.join(CERTS_DIR, f"{unique_id}.crt")
        cert_conf_file = os.path.join(CERTS_DIR, f"{unique_id}_cert.conf")

        # Calculate Expiry Date
        expiry_date = datetime.utcnow() + timedelta(days=cert_data.validity_days)

        # DEBUGGING LOGS
        print(f"Generating certificate for: {cert_data.dict()}")
        print(f"Files: {private_key_file}, {csr_file}, {cert_file}, {cert_conf_file}")
        print(f"Expiry Date: {expiry_date}")

        # Generate Private Key
        subprocess.run(["openssl", "genrsa", "-out", private_key_file, "2048"], check=True)
        print(f"Private key generated: {private_key_file}")

        # Create CSR Config File
        conf_content = f"""
        [req]
        default_bits       = 2048
        prompt             = no
        default_md         = sha256
        distinguished_name = req_distinguished_name
        req_extensions     = req_ext

        [req_distinguished_name]
        C  = {cert_data.country}
        ST = {cert_data.state}
        L  = {cert_data.locality}
        O  = {cert_data.organization}
        OU = {cert_data.organization_unit}
        CN = {cert_data.common_name}

        [req_ext]
        subjectAltName = @alt_names

        [alt_names]
        DNS.1 = {cert_data.subject_alt_name}
        """
        with open(cert_conf_file, "w") as conf_file:
            conf_file.write(conf_content)

        # DEBUG: Check if config file is created correctly
        with open(cert_conf_file, "r") as conf_file:
            print("Generated OpenSSL Config:\n", conf_file.read())

        # Generate CSR
        subprocess.run([
            "openssl", "req", "-new", "-key", private_key_file, "-out", csr_file, "-config", cert_conf_file
        ], check=True)
        print(f"CSR generated: {csr_file}")

        # Sign the CSR
        subprocess.run([
            "openssl", "x509", "-req", "-in", csr_file, "-CA", ROOT_CA_CERT, "-CAkey", ROOT_CA_KEY,
            "-CAcreateserial", "-out", cert_file, "-days", str(cert_data.validity_days), "-extfile", cert_conf_file
        ], check=True)
        print(f"Certificate generated: {cert_file}")

        # DEBUG: Check if certificate is generated
        if not os.path.exists(cert_file):
            raise HTTPException(status_code=500, detail="Certificate file was not generated!")

        # Store certificate details in MongoDB
        cert_collection.insert_one({
            "common_name": cert_data.common_name,
            "organization": cert_data.organization,
            "validity_days": cert_data.validity_days,
            "expiry_date": expiry_date.strftime("%Y-%m-%d %H:%M:%S"),  # Store as readable string
            "certificate_path": cert_file,
            "private_key_path": private_key_file,
            "csr_path": csr_file,
            "download_link": f"/download-certificate/{unique_id}"
        })

        return {
            "message": "Certificate generated successfully!",
            "expiry_date": expiry_date.strftime("%Y-%m-%d %H:%M:%S"),
            "download_url": f"http://127.0.0.1:8000/download-certificate/{unique_id}"
        }

    except subprocess.CalledProcessError as e:
        print(f"OpenSSL error: {e}")
        print(traceback.format_exc())  # Print full error details
        raise HTTPException(status_code=500, detail=f"OpenSSL error: {e}")

    except Exception as e:
        print(f"Unexpected error: {e}")
        print(traceback.format_exc())  # Print full error details
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")

@app.get("/download-certificate/{cert_id}")
def download_certificate(cert_id: str):
    cert_path = os.path.join(CERTS_DIR, f"{cert_id}.crt")

    
    # Debugging: log the certificate path
    print(f"Attempting to download certificate from: {cert_path}")
    
    # Check if the certificate exists
    if not os.path.exists(cert_path):
        raise HTTPException(status_code=404, detail="Certificate not found")

    # Returning the file response with appropriate headers
    return FileResponse(
        cert_path, 
        media_type="application/x-x509-ca-cert",  # MIME type for certificates
        filename=f"{cert_id}.crt",  # Filename to be used when downloading
        headers={"Content-Disposition": f"attachment; filename={cert_id}.crt"}  # Forces download
    )
@app.get("/certificates")
def get_certificates():
    certificates = list(cert_collection.find({}, {"_id": 1, "common_name": 1, "organization": 1, "expiry_date": 1}))

    # Convert ObjectId to string for frontend compatibility
    for cert in certificates:
        cert["_id"] = str(cert["_id"])

    return {"certificates": certificates}
# Path to the Root CA certificate
ROOT_CA_CERT = "generated_certs/rootCA.crt"

def get_ca_name():
    """Extract only the CA name (issuer) from the certificate"""
    try:
        issuer = subprocess.check_output(["openssl", "x509", "-in", ROOT_CA_CERT, "-noout", "-issuer"]).decode().strip()
        return {"ca_name": issuer.replace("issuer=", "").strip()}
    except Exception as e:
        return {"error": str(e)}

@app.get("/ca-name")
def get_ca_info():
    """API endpoint to get CA name"""
    return get_ca_name()

@app.get("/download-ca")
def download_ca():
    """API endpoint to download the Root CA certificate"""
    if os.path.exists(ROOT_CA_CERT):
        return FileResponse(ROOT_CA_CERT, filename="rootCA.crt", media_type="application/x-x509-ca-cert")
    return {"error": "CA certificate not found"}
