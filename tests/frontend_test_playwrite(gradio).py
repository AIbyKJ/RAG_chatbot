# test_gradio_load.py

import asyncio
import random
import logging
import os
from pathlib import Path
from playwright.async_api import async_playwright, expect, Page, Playwright
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter

# --- Configuration ---
GRADIO_URL = os.getenv("GRADIO_URL", "http://127.0.0.1:7860")
NUM_USERS = 1
ACTIONS_PER_MINUTE = 5 # Each "action" is a full workflow (chat, upload, or ingest)
TOTAL_DURATION_MINUTES = 2 # How long the test should run
PDF_UPLOAD_DIR = Path("temp_test_pdfs")

# --- Logging Setup ---
# A custom logger to include the user ID in each message
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - [User-%(user_id)s] - %(message)s',
)

# --- Helper Functions ---
def get_user_credentials(user_id: int):
    """Generates credentials for a specific user ID."""
    return f"testuser{user_id}", "password" # Use a secure, consistent password

def create_dummy_pdf(user_id: int, request_num: int) -> Path:
    """Creates a unique dummy PDF file for each upload action."""
    PDF_UPLOAD_DIR.mkdir(exist_ok=True)
    file_path = PDF_UPLOAD_DIR / f"user_{user_id}_doc_{request_num}.pdf"
    c = canvas.Canvas(str(file_path), pagesize=letter)
    c.drawString(100, 750, f"This is a test document for user {user_id}.")
    c.drawString(100, 735, f"Upload action number: {request_num}.")
    c.save()
    return file_path

# --- Playwright Automation Functions for Gradio ---

async def perform_login(page: Page, username: str, password: str, logger: logging.LoggerAdapter):
    """Handles the login flow for the Gradio application."""
    await page.goto(GRADIO_URL)
    logger.info("On login page, entering credentials...")

    # Wait for the login form to be fully visible
    await expect(page.get_by_label("Username")).to_be_visible(timeout=15000)

    # ❗ CORRECTED LINE: Use get_by_role for a precise match
    await page.get_by_role("radio", name="User").check()
    
    await page.get_by_label("Username").fill(username)
    await page.get_by_label("Password").fill(password)

    login_button = page.get_by_role("button", name="Login")
    await expect(login_button).to_be_enabled()
    await login_button.click()

    # Verify successful login by looking for the User Dashboard view
    user_dashboard_header = page.get_by_role("heading", name="👋 User Dashboard")
    await expect(user_dashboard_header).to_be_visible(timeout=20000)
    logger.info("Login successful. Navigated to User Dashboard.")


async def perform_chat(page: Page, logger: logging.LoggerAdapter, request_num: int):
    """Simulates a single chat interaction in the Gradio UI."""
    await page.get_by_role("tab", name="Chat").click()
    
    chat_input = page.get_by_placeholder("Type a message and press Enter...")
    await expect(chat_input).to_be_visible()

    message = f"What is the capital of France? (request #{request_num})"
    await chat_input.fill(message)
    await chat_input.press("Enter") # .submit() event in Gradio is triggered by Enter

    # A good way to confirm a response is to wait for the input to be cleared
    await expect(chat_input).to_be_empty(timeout=30000)
    logger.info(f"Chat request #{request_num} completed.")


async def perform_upload(page: Page, logger: logging.LoggerAdapter, user_id: int, request_num: int) -> str:
    """Simulates uploading a single PDF file in the Gradio UI."""
    await page.get_by_role("tab", name="Data Management").click()
    await page.get_by_role("tab", name="Upload PDFs (Files)").click()

    # Gradio's file input is often a simple <input type="file">
    pdf_path = create_dummy_pdf(user_id, request_num)
    file_input_selector = 'input[type="file"]'
    
    # We need to find the file input within the currently visible tab panel
    visible_tab_panel = page.locator('div[role="tabpanel"]:not([hidden])')
    await visible_tab_panel.locator(file_input_selector).set_input_files(pdf_path)

    await expect(page.get_by_text(pdf_path.name)).to_be_visible()
    
    # Use 'exact=True' to avoid clicking "Upload Folder Contents" by mistake
    await page.get_by_role("button", name="Upload", exact=True).click()
    
    # Wait for a success message (adjust text based on your app's actual output)
    await expect(page.get_by_text("Success:")).to_be_visible(timeout=20000)
    logger.info(f"File upload for '{pdf_path.name}' submitted successfully.")
    
    return pdf_path.name


async def perform_ingestion(page: Page, logger: logging.LoggerAdapter, pdf_name: str):
    """Simulates ingesting the most recently uploaded PDF."""
    await page.get_by_role("tab", name="VectorDB Management").click()
    await page.get_by_role("tab", name="Ingest My PDFs").click()
    
    # The 'select' event on the tab refreshes the dropdown. This click ensures it's fresh.
    ingest_one_button = page.get_by_role("button", name="Ingest Selected PDF")
    await expect(ingest_one_button).to_be_visible()
    
    # Gradio dropdowns are often a label + textbox combo
    dropdown = page.get_by_label("Select one of your PDFs to ingest")
    await dropdown.click()
    
    # Wait for the option to appear and click it
    await page.get_by_role("option", name=pdf_name).click()
    
    await ingest_one_button.click()
    
    await expect(page.get_by_text("Success:")).to_be_visible(timeout=30000)
    logger.info(f"Ingestion for '{pdf_name}' submitted successfully.")


# --- Main Simulation Function ---

async def simulate_user_session(playwright: Playwright, user_id: int):
    """
    Simulates a single user's entire session, performing a variety of tasks randomly.
    """
    logger = logging.LoggerAdapter(logging.getLogger(), {'user_id': user_id})
    username, password = get_user_credentials(user_id)
    browser = None
    page = None
    
    try:
        browser = await playwright.chromium.launch(headless=False)
        context = await browser.new_context()
        page = await context.new_page()
        logger.info("Browser launched.")

        await perform_login(page, username, password, logger)
        
        total_actions = ACTIONS_PER_MINUTE * TOTAL_DURATION_MINUTES
        wait_time_between_actions = 60.0 / ACTIONS_PER_MINUTE
        last_uploaded_pdf = None

        for i in range(total_actions):
            # Prioritize upload first to ensure there's something to ingest
            action = random.choice(["chat", "upload", "upload", "ingest"])
            
            if action == "upload":
                last_uploaded_pdf = await perform_upload(page, logger, user_id, i + 1)
            elif action == "ingest" and last_uploaded_pdf:
                await perform_ingestion(page, logger, last_uploaded_pdf)
            else: # Default to 'chat' if ingestion isn't possible
                await perform_chat(page, logger, i + 1)
            
            logger.info(f"Action #{i+1} completed. Waiting for {wait_time_between_actions:.1f}s...")
            await asyncio.sleep(wait_time_between_actions)

    except Exception as e:
        logger.error(f"An error occurred during the session: {e}", exc_info=True)
        if page:
            await page.screenshot(path=f"failure_user_{user_id}.png")
    finally:
        if browser:
            await browser.close()
            logger.info("Browser closed.")


async def main():
    """
    The main function that launches all concurrent user simulations.
    """
    print(f"--- Starting Gradio UI Load Test ---")
    print(f"Simulating {NUM_USERS} concurrent users.")
    print(f"Targeting {ACTIONS_PER_MINUTE} actions per minute per user.")
    print(f"Test will run for {TOTAL_DURATION_MINUTES} minute(s).")
    print(f"Target URL: {GRADIO_URL}")
    print("------------------------------------")

    async with async_playwright() as playwright:
        tasks = [simulate_user_session(playwright, i + 1) for i in range(NUM_USERS)]
        await asyncio.gather(*tasks)
    
    print("--- Gradio UI Load Test Finished ---")
    if PDF_UPLOAD_DIR.exists():
        for f in PDF_UPLOAD_DIR.glob("*.pdf"):
            f.unlink()
        PDF_UPLOAD_DIR.rmdir()
        print("Cleaned up temporary PDF files.")


if __name__ == "__main__":
    asyncio.run(main())