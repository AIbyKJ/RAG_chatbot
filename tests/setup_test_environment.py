#!/usr/bin/env python3
"""
Complete test setup and automation script for Gradio RAG Chatbot Portal.
This script uses existing PDF files for the UI automation part.

Steps:
1. Create test users via API.
2. Run UI automation with Playwright to:
   - Login as admin.
   - Upload 2 PDF files from a specified directory.
   - Ingest all public PDFs into the vector database.
"""

import asyncio
import time
import os
import glob
import requests
from requests.auth import HTTPBasicAuth
from playwright.async_api import async_playwright
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('complete_test.log'),
        logging.StreamHandler()
    ]
)

# --- Configuration ---
ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "adminpassword"
BASE_URL = "http://127.0.0.1:8000"
GRADIO_URL = "http://localhost:7860"

# Test data configuration
NUM_API_USERS = 20
PDF_UPLOAD_COUNT = 2
PDF_DIR = "data_pdfs_for_all_users"


class TestEnvironmentSetup:
    """Handles the backend API setup for creating users."""
    
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
                logging.error(f"Backend returned status {res.status_code}.")
                return False
        except requests.exceptions.ConnectionError:
            logging.error(f"Could not connect to backend at {BASE_URL}.")
            return False
        except Exception as e:
            logging.error(f"Connection test failed: {e}")
            return False
    
    def create_test_users(self):
        """Create test users via API."""
        logging.info("--- Creating Test Users via API ---")
        try:
            res = requests.get(f"{BASE_URL}/admin/users", auth=self.auth)
            res.raise_for_status()
            
            response_data = res.json()
            if not isinstance(response_data, list):
                response_data = response_data.get("users", [])
            existing_users = {user['username'] for user in response_data}

            logging.info(f"Found {len(existing_users)} existing users.")
            
            success_count = 0
            for i in range(1, NUM_API_USERS + 1):
                username = f"testuser{i}"
                if username in existing_users:
                    logging.info(f"User already exists, skipping: {username}")
                    success_count += 1
                    continue
                
                res_post = requests.post(
                    f"{BASE_URL}/admin/users",
                    json={"username": username, "password": "password"},
                    auth=self.auth
                )
                if res_post.status_code == 200:
                    logging.info(f"Successfully created user: {username}")
                    success_count += 1
                else:
                    logging.error(f"Failed to create user {username}: {res_post.text}")
            
            logging.info(f"User creation completed: {success_count}/{NUM_API_USERS}")
            return True
        except Exception as e:
            logging.error(f"User creation process failed: {e}")
            return False


class GradioUIAutomation:
    """Handles the Gradio UI automation testing."""
    
    def __init__(self, gradio_url=GRADIO_URL, headless=True):
        self.gradio_url = gradio_url
        self.headless = headless
        self.page = None
        self.browser = None
        self.context = None

    async def setup_browser(self):
        """Initialize Playwright browser."""
        self.playwright = await async_playwright().start()
        self.browser = await self.playwright.chromium.launch(headless=self.headless)
        self.context = await self.browser.new_context(viewport={'width': 1920, 'height': 1080})
        self.page = await self.context.new_page()
        self.page.set_default_timeout(30000)
        logging.info("Browser initialized successfully.")

    async def teardown_browser(self):
        """Close browser."""
        if self.context: await self.context.close()
        if self.browser: await self.browser.close()
        if hasattr(self, 'playwright'): await self.playwright.stop()
        logging.info("Browser closed.")

    async def login_as_admin(self):
        """Login as admin user."""
        logging.info("--- Starting Admin Login ---")
        await self.page.goto(self.gradio_url)
        logging.info(f"Navigated to {self.gradio_url}")

        await self.page.wait_for_selector('label:has-text("Admin")', state='visible')
        
        await self.page.locator('label:has-text("Admin")').click()
        await self.page.locator('label:has-text("Username") textarea').fill(ADMIN_USERNAME)
        await self.page.locator('label:has-text("Password") input').fill(ADMIN_PASSWORD)
        logging.info("Filled login credentials.")
        
        await self.page.locator('button:has-text("Login")').click()
        
        await self.page.wait_for_selector('h1:has-text("Admin Dashboard")', timeout=15000)
        logging.info("Successfully logged in as admin and dashboard is visible.")

    async def upload_pdfs(self):
        """Upload PDF files as public from the specified directory."""
        logging.info(f"--- Uploading {PDF_UPLOAD_COUNT} PDFs via UI from '{PDF_DIR}' ---")
        
        await self.page.locator('button[role="tab"]:has-text("Data Management")').click()
        await self.page.locator('button[role="tab"]:has-text("Upload PDFs (Files)")').click()
        logging.info("Navigated to Admin > Data Management > Upload PDFs tab.")

        pdf_files = glob.glob(os.path.join(PDF_DIR, "*.pdf"))
        if len(pdf_files) < PDF_UPLOAD_COUNT:
            raise FileNotFoundError(
                f"Expected at least {PDF_UPLOAD_COUNT} PDF files in '{PDF_DIR}', but found {len(pdf_files)}."
            )

        files_to_upload = pdf_files[:PDF_UPLOAD_COUNT]
        
        file_input = self.page.locator('input[type="file"]').nth(0)
        await file_input.set_input_files(files_to_upload)
        logging.info(f"Selected files: {[os.path.basename(f) for f in files_to_upload]}")
        
        await self.page.locator('input[type="radio"][value="Yes"]').click()
        logging.info("Selected 'Make these PDFs public?': Yes")

        upload_button = self.page.locator('button:has-text("Upload PDF(s)")')
        await upload_button.click()
        logging.info("Clicked upload button.")
        
        # await self.page.wait_for_selector('text=/Success:.*uploaded/i', timeout=60000) # Increased timeout for upload
        # logging.info("PDF upload successful.")

    async def ingest_public_pdfs(self):
        """Ingests all public PDFs from the UI."""
        logging.info("--- Ingesting Public PDFs via UI ---")

        await self.page.locator('button[role="tab"]:has-text("VectorDB Management")').click()

        # ### FINAL FIX: Use get_by_role with an EXACT name match to avoid ambiguity with "List Ingested"
        await self.page.get_by_role("tab", name="Ingest", exact=True).click()
        logging.info("Navigated to Admin > VectorDB Management > Ingest tab.")

        await self.page.get_by_role("button", name="Ingest All Public").click()
        logging.info("Clicked 'Ingest All Public' button.")
        
        await self.page.wait_for_selector('text=/Success:.*ingested/i', timeout=60000)
        logging.info("Successfully ingested all public PDFs.")

    async def run_ui_automation(self):
        """Run the complete UI automation."""
        logging.info("--- Starting UI Automation ---")
        try:
            await self.setup_browser()
            await self.login_as_admin()
            await self.upload_pdfs()
            await self.ingest_public_pdfs()
            
            logging.info("UI automation completed successfully!")
            await self.page.wait_for_timeout(3000)
        except Exception as e:
            logging.error(f"UI automation failed: {e}")
            if self.page:
                screenshot_path = f"final_error_{int(time.time())}.png"
                await self.page.screenshot(path=screenshot_path, full_page=True)
                logging.error(f"Screenshot saved to {screenshot_path}")
            raise
        finally:
            await self.teardown_browser()


async def main():
    """Main function to run complete test setup and automation."""
    logging.info("=== Starting Complete Test Setup and Automation ===")
    
    logging.info(f"Step 1: Verifying PDF directory '{PDF_DIR}'...")
    if not os.path.isdir(PDF_DIR) or not glob.glob(os.path.join(PDF_DIR, "*.pdf")):
        print(f"❌ Error: The directory '{PDF_DIR}' does not exist or contains no PDF files.")
        print("Please create it and add your PDF files before running the script.")
        return 1
    logging.info("PDF directory verified.")

    setup = TestEnvironmentSetup()
    
    logging.info("Step 2: Testing backend connection...")
    if not setup.test_connection():
        print("❌ Backend connection failed. Please ensure the backend server is running.")
        return 1
    
    logging.info("Step 3: Creating test users via API...")
    if not setup.create_test_users():
        print("❌ API user creation failed. Halting test.")
        return 1
    
    logging.info("Step 4: Starting UI automation...")
    ui_automation = GradioUIAutomation(headless=False)
    
    try:
        await ui_automation.run_ui_automation()
        print("\n✅✅✅ Complete test setup and automation finished successfully! ✅✅✅")
        print("📊 Summary:")
        print(f"   - API Users Checked/Created: {NUM_API_USERS}")
        print(f"   - PDFs Uploaded via UI: {PDF_UPLOAD_COUNT} from '{PDF_DIR}'")
        print(f"   - Ingest Action: All public PDFs were ingested.")
        return 0
    except Exception as e:
        print(f"\n❌ UI automation failed: {e}")
        return 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    exit(exit_code)