#!/usr/bin/env python3
"""
Backend Test Environment Setup for Streamlit UI

This script prepares the backend by creating test users, uploading public PDF files,
and ingesting them into the vector database. It should be run before executing 
the Playwright UI tests.
"""

import requests
from requests.auth import HTTPBasicAuth
import logging
import os
import glob
from pathlib import Path

# --- Configuration ---
ADMIN_USERNAME = os.getenv("ADMIN_USERNAME", "admin")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "adminpassword")
BASE_URL = os.getenv("BASE_URL", "http://127.0.0.1:8000")
NUM_API_USERS = 2 # Number of test users to create (e.g., testuser1, testuser2)
# Directory containing PDFs to be uploaded and ingested as public
PDF_PUBLIC_DIR = Path("./data_pdfs_for_all_users") 

# --- Logging Setup ---
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
)

class TestEnvironmentSetup:
    """Handles the backend API setup for users, files, and ingestion."""
    
    def __init__(self):
        self.auth = HTTPBasicAuth(ADMIN_USERNAME, ADMIN_PASSWORD)
    
    def test_connection(self):
        """Test if the backend is accessible."""
        try:
            res = requests.get(f"{BASE_URL}/admin/auth/check", auth=self.auth, timeout=5)
            if res.status_code == 200:
                logging.info("Backend connection successful.")
                return True
            else:
                logging.error(f"Backend connection failed with status {res.status_code}: {res.text}")
                return False
        except requests.exceptions.ConnectionError:
            logging.error(f"Could not connect to backend at {BASE_URL}. Is the server running?")
            return False
        except Exception as e:
            logging.error(f"An unexpected error occurred during connection test: {e}")
            return False
    
    def create_test_users(self):
        """Creates test users via API if they don't already exist."""
        logging.info("--- Starting Test User Creation via API ---")
        try:
            res = requests.get(f"{BASE_URL}/admin/users", auth=self.auth)
            res.raise_for_status()
            
            response_data = res.json()
            if isinstance(response_data, dict):
                response_data = response_data.get("users", [])
            
            existing_users = {user['username'] for user in response_data}
            logging.info(f"Found {len(existing_users)} existing users.")
            
            created_count = 0
            for i in range(1, NUM_API_USERS + 1):
                username = f"testuser{i}"
                if username in existing_users:
                    logging.info(f"User '{username}' already exists, skipping.")
                    continue
                
                res_post = requests.post(
                    f"{BASE_URL}/admin/users",
                    json={"username": username, "password": "password"},
                    auth=self.auth
                )
                
                if res_post.status_code == 200:
                    logging.info(f"Successfully created user: '{username}'")
                    created_count += 1
                else:
                    logging.error(f"Failed to create user '{username}': {res_post.text}")
            
            logging.info(f"User creation process completed. Created {created_count} new user(s).")
            return True
        except requests.exceptions.RequestException as e:
            logging.error(f"An API error occurred during user creation: {e}")
            return False
        except Exception as e:
            logging.error(f"An unexpected error occurred during user creation: {e}")
            return False

    def upload_and_ingest_pdfs(self):
        """Uploads all PDFs from the public directory and then ingests them."""
        logging.info("--- Starting PDF Upload and Ingestion Process ---")
        
        # Step 1: Upload PDFs
        if not PDF_PUBLIC_DIR.is_dir():
            logging.error(f"PDF directory not found: {PDF_PUBLIC_DIR}")
            return False
        
        pdf_files = glob.glob(str(PDF_PUBLIC_DIR / "*.pdf"))
        if not pdf_files:
            logging.warning(f"No PDF files found in {PDF_PUBLIC_DIR}, skipping upload and ingest.")
            return True # Not a failure, just nothing to do.

        files_to_upload = [
            ("files", (Path(f).name, open(f, "rb"), "application/pdf")) for f in pdf_files
        ]
        # Form data to mark these files as public
        data_payload = {"is_public": 1}

        try:
            logging.info(f"Uploading {len(pdf_files)} public PDF(s) to the backend...")
            res_upload = requests.post(
                f"{BASE_URL}/admin/pdf/upload",
                files=files_to_upload,
                data=data_payload,
                auth=self.auth,
                timeout=60 # Allow ample time for uploads
            )
            res_upload.raise_for_status()
            logging.info("PDF upload successful.")
        except requests.exceptions.RequestException as e:
            logging.error(f"Failed to upload PDFs: {e}")
            return False
        finally:
            # Ensure file handles are closed
            for _, (_, f, _) in files_to_upload:
                f.close()

        # Step 2: Ingest all public PDFs
        try:
            logging.info("Triggering ingestion of all public PDFs...")
            res_ingest = requests.post(
                f"{BASE_URL}/admin/vectordb/ingest/all",
                auth=self.auth,
                timeout=90 # Ingestion can be slow
            )
            res_ingest.raise_for_status()
            logging.info("PDF ingestion command sent successfully.")
            return True
        except requests.exceptions.RequestException as e:
            logging.error(f"Failed to ingest PDFs: {e}")
            return False

def main():
    """Main function to run the setup."""
    print("--- Preparing Backend for Streamlit UI Test ---")
    setup = TestEnvironmentSetup()
    
    print("\nStep 1: Testing backend connection...")
    if not setup.test_connection():
        print("❌ Backend connection failed. Please ensure the backend server is running and credentials are correct.")
        return 1
    
    print("\nStep 2: Creating test users via API...")
    if not setup.create_test_users():
        print("❌ API user creation failed. Halting setup.")
        return 1

    print("\nStep 3: Uploading and ingesting public PDFs via API...")
    if not setup.upload_and_ingest_pdfs():
        print("❌ PDF upload and ingestion failed. Halting setup.")
        return 1
        
    print("\n✅ Backend environment setup is complete.")
    return 0

if __name__ == "__main__":
    exit_code = main()
    exit(exit_code)
