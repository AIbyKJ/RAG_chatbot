# test_gradio_workflow.py

import asyncio
import logging
import os
from pathlib import Path
from playwright.async_api import async_playwright, expect, Page, Playwright
import glob

# --- Configuration ---
GRADIO_URL = os.getenv("GRADIO_URL", "http://127.0.0.1:7860")
NUM_USERS = 2
PDF_BASE_DIR = Path("./")
CHAT_LOG_DIR = Path("./chat_logs")

# --- NEW: Specific questions to ask in the chat workflow ---
CHAT_QUESTIONS = [
    "who is elara",
    "my name sander",
    "Senior AI Engineer with 8 years of experience leading the development",
    "Designed and implemented AI-Driven Expert Matching feature for Expert Network Platform using React,",
    "what did Barnaby Emporium",
    "who is ALEKSANDAR VASIC,",
    "what did worked as a lead researcher at NexaCorp,"
]

# --- Logging Setup ---
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - [User-%(user_id)s] - %(message)s',
)

# --- Helper Functions ---
def get_user_credentials(user_id: int):
    """Generates credentials for a specific user ID."""
    return f"testuser{user_id}", "password"

# --- Playwright Automation Functions for Gradio ---

async def perform_login(page: Page, username: str, password: str, logger: logging.LoggerAdapter):
    """Handles the login flow for the Gradio application."""
    await page.goto(GRADIO_URL)
    logger.info(f"On login page, attempting to log in as '{username}'...")
    await expect(page.get_by_label("Username")).to_be_visible(timeout=15000)
    await page.get_by_role("radio", name="User").check()
    await page.get_by_label("Username").fill(username)
    await page.get_by_label("Password").fill(password)
    login_button = page.get_by_role("button", name="Login")
    await expect(login_button).to_be_enabled()
    await login_button.click()
    user_dashboard_header = page.get_by_role("heading", name="👋 User Dashboard")
    await expect(user_dashboard_header).to_be_visible(timeout=20000)
    logger.info("Login successful. Navigated to User Dashboard.")

async def perform_upload_all_pdfs(page: Page, logger: logging.LoggerAdapter, user_id: int):
    """Finds all PDFs in the user's directory and uploads them."""
    user_pdf_dir = PDF_BASE_DIR / f"data_user{user_id}_pdfs"
    if not user_pdf_dir.is_dir():
        logger.warning(f"PDF directory not found for user, skipping upload: {user_pdf_dir}")
        return
    pdf_files = glob.glob(str(user_pdf_dir / "*.pdf"))
    if not pdf_files:
        logger.warning(f"No PDF files found in {user_pdf_dir}, skipping upload.")
        return
    logger.info(f"Found {len(pdf_files)} PDF(s) to upload from {user_pdf_dir}.")
    await page.get_by_role("tab", name="Data Management").click()
    await page.get_by_role("tab", name="Upload PDFs (Files)").click()
    logger.info("Navigated to the PDF upload tab.")
    visible_tab_panel = page.locator('div[role="tabpanel"]:not([hidden])')
    await visible_tab_panel.locator('input[type="file"]').set_input_files(pdf_files)
    await page.get_by_role("button", name="Upload", exact=True).click()
    await expect(page.get_by_text("Success:")).to_be_visible(timeout=60000)
    logger.info(f"Successfully uploaded {len(pdf_files)} PDF(s).")

async def perform_ingest_all(page: Page, logger: logging.LoggerAdapter):
    """Simulates ingesting all of the user's uploaded PDFs."""
    logger.info("Starting ingestion of all user PDFs.")
    await page.get_by_role("tab", name="VectorDB Management").click()
    await page.get_by_role("tab", name="Ingest My PDFs").click()
    ingest_all_button = page.get_by_role("button", name="Ingest All My PDFs")
    await expect(ingest_all_button).to_be_enabled()
    await ingest_all_button.click()
    await expect(page.get_by_text("Success:")).to_be_visible(timeout=90000)
    logger.info("Ingestion of all user PDFs submitted successfully.")

async def perform_chat_and_save_history(page: Page, logger: logging.LoggerAdapter, user_id: int):
    """Simulates a multi-turn chat conversation and saves the full history to a file."""
    logger.info("Starting chat conversation.")
    
    # ### FINAL FIX: Use exact=True to distinguish "Chat" from "Clear My Chat Memory"
    await page.get_by_role("tab", name="Chat", exact=True).click()
    
    chat_input = page.get_by_placeholder("Type a message and press Enter...")
    await expect(chat_input).to_be_visible()

    # The main container for the chatbot messages
    chatbot_container = page.locator(".bubble-wrap")

    for i, message in enumerate(CHAT_QUESTIONS):
        await chat_input.fill(message)
        await chat_input.press("Enter")
        logger.info(f"Sent message #{i+1}: '{message}'")
        
        # Dynamically wait for the next pair of messages (user + bot) to appear
        # After sending the (i+1)th message, we expect (i+1)*2 total message bubbles
        expected_message_count = (i + 1) * 2
        await expect(chatbot_container.locator("div[data-testid='user'], div[data-testid='bot']")).to_have_count(
            expected_message_count, timeout=60000
        )
        logger.info(f"Bot response #{i+1} received.")

    # Scrape and save the history after all questions are asked
    CHAT_LOG_DIR.mkdir(exist_ok=True)
    history_log_path = CHAT_LOG_DIR / f"chat_history_user_{user_id}.log"
    
    # This selector finds all divs that represent a user message or a bot message
    all_message_bubbles = await chatbot_container.locator("div[data-testid='user'], div[data-testid='bot']").all()
    
    with open(history_log_path, "w", encoding="utf-8") as f:
        f.write(f"Chat History for user{user_id} at {logging.Formatter().formatTime(logging.makeLogRecord({}))}\n")
        f.write("="*80 + "\n")
        for bubble in all_message_bubbles:
            # Check the data-testid attribute to determine if it's a user or bot message
            role = await bubble.get_attribute("data-testid")
            text = await bubble.inner_text()
            f.write(f"{role.upper()}: {text}\n")
            f.write("-"*80 + "\n")
            
    logger.info(f"Full chat history saved to {history_log_path}")

async def simulate_user_workflow(playwright: Playwright, user_id: int):
    """Simulates a single user's entire fixed workflow."""
    logger = logging.LoggerAdapter(logging.getLogger(), {'user_id': user_id})
    username, password = get_user_credentials(user_id)
    browser = None
    page = None
    
    try:
        browser = await playwright.chromium.launch(headless=False) # Set to False to watch the test run
        context = await browser.new_context()
        page = await context.new_page()
        logger.info("Browser launched.")

        # --- Execute the Workflow ---
        await perform_login(page, username, password, logger)
        await perform_upload_all_pdfs(page, logger, user_id)
        await perform_ingest_all(page, logger)
        await perform_chat_and_save_history(page, logger, user_id)
        
        logger.info("User workflow completed successfully.")

    except Exception as e:
        logger.error(f"An error occurred during the workflow: {e}", exc_info=True)
        if page:
            await page.screenshot(path=f"failure_user_{user_id}.png", full_page=True)
    finally:
        if browser:
            await browser.close()
            logger.info("Browser closed.")

async def main():
    """The main function that launches all concurrent user simulations."""
    print(f"--- Starting Gradio UI Workflow Test ---")
    print(f"Simulating a full workflow for {NUM_USERS} user(s).")
    print(f"Target URL: {GRADIO_URL}")
    print("-----------------------------------------")

    async with async_playwright() as playwright:
        tasks = [simulate_user_workflow(playwright, i + 1) for i in range(NUM_USERS)]
        await asyncio.gather(*tasks)
    
    print("--- Gradio UI Workflow Test Finished ---")
    print(f"Chat histories saved in '{CHAT_LOG_DIR}' directory.")


if __name__ == "__main__":
    CHAT_LOG_DIR.mkdir(exist_ok=True)
    asyncio.run(main())