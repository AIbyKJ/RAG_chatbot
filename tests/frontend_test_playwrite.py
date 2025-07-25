import asyncio
import random
import logging
import os
from pathlib import Path
from playwright.async_api import async_playwright, expect, Page, Playwright
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter

# --- Configuration ---
STREAMLIT_URL = os.getenv("FRONTEND_URL", "http://localhost:8501")
NUM_USERS = 20
ACTIONS_PER_MINUTE = 5 # Each "action" is a full workflow (chat, upload, or ingest)
TOTAL_DURATION_MINUTES = 2 # How long the test should run
PDF_UPLOAD_DIR = Path("temp_test_pdfs")

# --- Logging Setup ---
# logging.basicConfig(
#     level=logging.INFO,
#     format='%(asctime)s - %(levelname)s - [User-%(user_id)s] - %(message)s',
# )

# --- Helper Functions ---
def get_user_credentials(user_id: int):
    """Generates credentials for a specific user ID."""
    return f"testuser{user_id}", "password"

def create_dummy_pdf(user_id: int, request_num: int) -> Path:
    """Creates a unique dummy PDF for each upload action."""
    PDF_UPLOAD_DIR.mkdir(exist_ok=True)
    file_path = PDF_UPLOAD_DIR / f"user_{user_id}_doc_{request_num}.pdf"
    c = canvas.Canvas(str(file_path), pagesize=letter)
    c.drawString(100, 750, f"This is a test document for user {user_id}.")
    c.drawString(100, 735, f"Upload action number: {request_num}.")
    c.save()
    return file_path

# --- Playwright Automation Functions ---

async def perform_login_and_navigate(page: Page, username: str, password: str):
    """Handles the login flow and navigates to the main user dashboard."""
    await page.goto(STREAMLIT_URL)
    
    # --- Login on Home.py ---
    logger.info("On login page, selecting role and entering credentials...")
    
    await page.get_by_role("radiogroup", name="Select role").get_by_text("User").click()
    logger.info("Selected 'User' role.")

    await page.get_by_label("Username").fill(username)
    await page.get_by_role("textbox", name="Password").fill(password)

    login_button = page.get_by_role("button", name="Login")
    await expect(login_button).to_be_enabled()
    await login_button.click()
    logger.info("Login button clicked.")

    await expect(login_button).to_be_hidden(timeout=15000)
    logger.info("Login form is hidden, confirming login process.")

    # --- Navigate to User Dashboard ---
    logger.info("Navigating to User Dashboard...")
    dashboard_link = page.get_by_role("link", name="User Dashboard")
    await expect(dashboard_link).to_be_visible(timeout=20000)
    await dashboard_link.click()
    
    # --- Verify Navigation and Sidebar Readiness ---
    welcome_header = page.get_by_role("heading", name=f"👋 Welcome, {username}!")
    await expect(welcome_header).to_be_visible(timeout=20000)
    
    sidebar_menu = page.get_by_role("radiogroup", name="User Menu")
    await expect(sidebar_menu).to_be_visible(timeout=30000)
    
    logger.info("Successfully navigated to User Dashboard and sidebar is ready.")


async def perform_chat(page: Page, request_num: int):
    """Simulates a single chat interaction."""
    logger.info("Navigating to Chat menu...")
    await page.get_by_role("radiogroup", name="User Menu").get_by_text("Chat").click()
    
    chat_messages = ["What is RAG?", "Explain vector search.", "Summarize my documents."]
    message = f"{random.choice(chat_messages)} (request #{request_num})"

    chat_input_container = page.get_by_test_id("stChatInput")
    chat_textarea = chat_input_container.locator("textarea")
    
    await expect(chat_textarea).to_be_visible()
    await chat_textarea.fill(message)
    
    send_button = chat_input_container.get_by_role("button")
    await expect(send_button).to_be_enabled()
    await send_button.click()
    
    assistant_response = page.locator('[data-testid="stChatMessage"]').last.get_by_test_id("stMarkdownContainer")
    await expect(assistant_response).not_to_be_empty(timeout=30000)
    logger.info(f"Chat request #{request_num} completed.")

async def perform_upload(page: Page, user_id: int, request_num: int) -> str:
    """Simulates uploading a single PDF file."""
    logger.info("Navigating to Data Management menu...")
    await page.get_by_role("radiogroup", name="User Menu").get_by_text("Data Management").click()
    
    await page.get_by_role("tab", name="Upload PDFs (Files)").click()
    
    upload_header = page.get_by_role("heading", name="Upload Your PDF Documents")
    await expect(upload_header).to_be_visible(timeout=15000)
    
    pdf_path = create_dummy_pdf(user_id, request_num)
    logger.info(f"Uploading file: {pdf_path.name}")
    
    visible_tab_panel = page.locator('div[role="tabpanel"]:not([hidden])')
    file_input = visible_tab_panel.get_by_test_id("stFileUploaderDropzoneInput")
    await file_input.set_input_files(pdf_path)
    
    await expect(page.get_by_text(pdf_path.name)).to_be_visible()
    
    await page.get_by_role("button", name="Upload Files").click()
    
    await page.wait_for_timeout(2000) 
    logger.info(f"File upload for {pdf_path.name} submitted.")
    
    return pdf_path.name

async def perform_ingestion(page: Page, pdf_name: str):
    """Simulates ingesting the most recently uploaded PDF."""
    logger.info("Navigating to VectorDB Management menu...")
    await page.get_by_role("radiogroup", name="User Menu").get_by_text("VectorDB Management").click()

    await page.get_by_role("tab", name="Ingest My PDFs").click()
    
    # Wait for the tab content to be ready
    ingest_header = page.get_by_role("heading", name="Ingest Your PDFs into the VectorDB")
    await expect(ingest_header).to_be_visible(timeout=15000)
    
    logger.info(f"Attempting to ingest file: {pdf_name}")
    
    # --- FINAL FIX: Scope the selectbox locator to the visible tab panel ---
    # 1. Find the currently visible tab panel.
    visible_tab_panel = page.locator('div[role="tabpanel"]:not([hidden])')
    
    # 2. Find the selectbox *only within that visible panel*.
    selectbox = visible_tab_panel.get_by_test_id("stSelectbox")
    await selectbox.click()
    
    await page.get_by_role("option", name=pdf_name).click()
    
    await page.get_by_role("button", name="Ingest Selected PDF").click()
    
    await page.wait_for_timeout(2000)
    logger.info(f"Ingestion for {pdf_name} submitted.")

# --- Main Simulation Function ---

async def simulate_user_session(playwright: Playwright, user_id: int):
    """
    Simulates a single user's entire session, performing a variety of tasks.
    """
    # logger = logging.LoggerAdapter(logging.getLogger(), {'user_id': user_id})
    username, password = get_user_credentials(user_id)
    browser = None
    page = None
    
    try:
        browser = await playwright.chromium.launch(headless=False)
        page = await browser.new_page()
        logger.info("Browser launched.")

        await perform_login_and_navigate(page, username, password, logger)
        
        total_actions = ACTIONS_PER_MINUTE * TOTAL_DURATION_MINUTES
        wait_time_between_actions = 60.0 / ACTIONS_PER_MINUTE
        last_uploaded_pdf = None

        for i in range(total_actions):
            action = random.choice(["chat", "upload", "ingest"])
            
            if action == "upload":
                last_uploaded_pdf = await perform_upload(page, logger, user_id, i + 1)
            elif action == "ingest" and last_uploaded_pdf:
                await perform_ingestion(page, logger, last_uploaded_pdf)
            else:
                await perform_chat(page, logger, i + 1)
            
            logger.info(f"Action #{i+1} completed. Waiting for next action...")
            await asyncio.sleep(wait_time_between_actions)

    except Exception as e:
        logger.error(f"An error occurred during the session: {e}")
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
    print(f"--- Starting UI Load Test ---")
    print(f"Simulating {NUM_USERS} concurrent users.")
    print(f"Targeting {ACTIONS_PER_MINUTE} full actions per minute per user.")
    print(f"Test will run for {TOTAL_DURATION_MINUTES} minute(s).")
    print(f"Target URL: {STREAMLIT_URL}")
    print("-----------------------------")

    async with async_playwright() as playwright:
        tasks = [simulate_user_session(playwright, i + 1) for i in range(NUM_USERS)]
        await asyncio.gather(*tasks)
    
    print("--- UI Load Test Finished ---")
    if PDF_UPLOAD_DIR.exists():
        for f in PDF_UPLOAD_DIR.glob("*.pdf"):
            f.unlink()
        PDF_UPLOAD_DIR.rmdir()
        print("Cleaned up temporary PDF files.")

if __name__ == "__main__":
    if os.name == 'nt':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(main())
