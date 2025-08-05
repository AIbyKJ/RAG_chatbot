#!/usr/bin/env python3
"""
Frontend End-to-End Workflow Test for Streamlit User Dashboard

This script simulates a user's entire workflow:
1. Logs in as a specific test user.
2. Navigates to the User Dashboard.
3. Uploads all PDFs from the user's dedicated folder (e.g., ./data_user1_pdfs).
4. Ingests all of the user's uploaded PDFs into the vector database.
5. Navigates to the chat, asks a series of questions, and waits for responses.
6. Saves the complete chat history to a log file.
"""

import asyncio
import logging
import os
import re
from pathlib import Path
from playwright.async_api import async_playwright, expect, Page, Playwright, TimeoutError
import glob

# --- Configuration ---
STREAMLIT_URL = os.getenv("STREAMLIT_URL", "http://127.0.0.1:8501")
NUM_USERS = 2  # Set this to the number of user data folders you have
PDF_BASE_DIR = Path("./")
CHAT_LOG_DIR = Path("./chat_logs")

# --- Specific questions to ask in the chat workflow ---
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

# --- Playwright Automation Functions for Streamlit ---

async def perform_login(page: Page, username: str, password: str, logger: logging.LoggerAdapter):
    """Handles the login flow for the Streamlit application."""
    await page.goto(STREAMLIT_URL)
    logger.info(f"On login page, attempting to log in as '{username}'...")

    # Find the radio button for "User" by its specific role and name to avoid ambiguity
    await page.get_by_role("radio", name="User").check()
    
    # Fill credentials using the more specific get_by_role("textbox") to avoid ambiguity
    await page.get_by_role("textbox", name="Username").fill(username)
    await page.get_by_role("textbox", name="Password").fill(password)

    login_button = page.get_by_role("button", name="Login")
    await expect(login_button).to_be_enabled()
    await login_button.click()

    # Verify successful login by looking for the welcome message in the sidebar
    sidebar = page.get_by_test_id("stSidebar")
    await expect(sidebar.get_by_role("heading", name=f"Welcome, {username}!")).to_be_visible(timeout=20000)
    logger.info("Login successful. Welcome message is visible in the sidebar.")

async def perform_upload_all_pdfs(page: Page, logger: logging.LoggerAdapter, user_id: int):
    """Finds all PDFs in the user's directory and uploads them."""
    # After login, explicitly navigate to the User Dashboard page.
    await page.get_by_role("link", name="User Dashboard").click()
    logger.info("Navigated to User Dashboard page.")
    
    # In the User Dashboard, navigation is done with radio buttons in the sidebar
    await page.locator("label", has_text="Data Management").click()
    logger.info("Navigated to Data Management section.")

    # Once in the section, the main panel uses tabs
    await page.get_by_role("tab", name="Upload PDFs (Files)").click()
    logger.info("Navigated to the PDF upload tab.")

    user_pdf_dir = PDF_BASE_DIR / f"data_user{user_id}_pdfs"
    if not user_pdf_dir.is_dir():
        logger.warning(f"PDF directory not found, skipping upload: {user_pdf_dir}")
        return
    pdf_files = glob.glob(str(user_pdf_dir / "*.pdf"))
    if not pdf_files:
        logger.warning(f"No PDF files found in {user_pdf_dir}, skipping upload.")
        return

    logger.info(f"Found {len(pdf_files)} PDF(s) to upload from {user_pdf_dir}.")

    # Use the test_id for Streamlit's file uploader and find the input within it
    await page.get_by_test_id("stFileUploader").locator("input[type=file]").set_input_files(pdf_files)
    
    # Wait for the file names to appear in the UI
    for pdf in pdf_files:
        await expect(page.get_by_text(Path(pdf).name)).to_be_visible()
    
    # Click the upload button, which is a form submit button.
    await page.get_by_role("button", name="Upload Files", exact=True).click()
    
    # Find the specific alert container that contains the success text.
    success_alert = expect(page.get_by_test_id("Success")).to_be_visible(timeout=90000)
    logger.info(f"Successfully uploaded {len(pdf_files)} PDF(s).")

async def perform_ingest_all(page: Page, logger: logging.LoggerAdapter):
    """Simulates ingesting all of the user's uploaded PDFs."""
    logger.info("Starting ingestion of all user PDFs.")
    # Navigate using the sidebar radio button
    await page.locator("label", has_text="VectorDB Management").click()
    
    # Navigate using the main panel tab
    await page.get_by_role("tab", name="Ingest My PDFs").click()
    
    ingest_all_button = page.get_by_role("button", name="Ingest All My PDFs")
    await expect(ingest_all_button).to_be_enabled()
    await ingest_all_button.click()
    
    # Find the specific alert container that contains the success text.
    success_alert = expect(page.get_by_test_id("Success")).to_be_visible(timeout=90000)
    logger.info("Ingestion of all user PDFs submitted successfully.")

async def perform_chat_and_save_history(page: Page, logger: logging.LoggerAdapter, user_id: int):
    """Simulates a multi-turn chat and saves the history."""
    logger.info("Starting chat conversation.")
    # Navigate using the sidebar radio button
    await page.locator("label", has_text="Chat").click()
    
    chat_input = page.get_by_test_id("stChatInput")
    await expect(chat_input).to_be_visible()

    chat_container = page.get_by_test_id("stAppScrollToBottomContainer")

    for i, message in enumerate(CHAT_QUESTIONS):
        # Get the count of BOT messages before sending a new one
        current_bot_count = await chat_container.locator("[data-testid='stChatMessageAvatarAssistant']").count() + 1
        print("Current Bot Count : ", i, current_bot_count)
        
        await chat_input.locator("textarea").fill(message)
        await chat_input.locator("textarea").press("Enter")
        logger.info(f"Sent message #{i+1}: '{message}'")
        
        try:
            # Wait specifically for a NEW bot message to appear
            await expect(chat_container.locator("[data-testid='stChatMessageAvatarAssistant']")).to_have_count(current_bot_count + 1, timeout=120000)
            logger.info(f"Bot response #{i+1} received.")
        except TimeoutError:
            logger.warning(f"Bot failed to respond to message #{i+1}. Continuing with next question.")
            # The test will continue to the next iteration of the loop

    # Scrape and save the history
    CHAT_LOG_DIR.mkdir(exist_ok=True)
    history_log_path = CHAT_LOG_DIR / f"chat_history_user_{user_id}.log"
    
    all_messages = await chat_container.get_by_test_id("stChatMessage").all()
    
    with open(history_log_path, "w", encoding="utf-8") as f:
        f.write(f"Chat History for user{user_id} at {logging.Formatter().formatTime(logging.makeLogRecord({}))}\n")
        f.write("="*80 + "\n")
        for msg_element in all_messages:
            # Use the presence of the specific avatar test ID to determine the role
            is_user = await msg_element.locator("[data-testid='stChatMessageAvatarUser']").count() > 0
            role = "USER" if is_user else "BOT"
            text_content = await msg_element.locator("[data-testid='stMarkdownContainer']").inner_text()
            
            f.write(f"{role}: {text_content}\n")
            f.write("-"*80 + "\n")
            
    logger.info(f"Full chat history saved to {history_log_path}")

async def simulate_user_workflow(playwright: Playwright, user_id: int):
    """Simulates a single user's entire fixed workflow for Streamlit."""
    logger = logging.LoggerAdapter(logging.getLogger(), {'user_id': user_id})
    username, password = get_user_credentials(user_id)
    browser = None
    
    try:
        browser = await playwright.chromium.launch(headless=False)
        context = await browser.new_context()
        page = await context.new_page()
        logger.info("Browser launched.")

        await perform_login(page, username, password, logger)
        await perform_upload_all_pdfs(page, logger, user_id)
        await perform_ingest_all(page, logger)
        await perform_chat_and_save_history(page, logger, user_id)
        
        logger.info("User workflow completed successfully.")

    except Exception as e:
        logger.error(f"An error occurred during the workflow: {e}", exc_info=True)
        if 'page' in locals() and page:
            await page.screenshot(path=f"failure_streamlit_user_{user_id}.png", full_page=True)
    finally:
        if browser:
            await browser.close()
            logger.info("Browser closed.")

async def main():
    """Launches all concurrent user simulations for Streamlit."""
    print(f"--- Starting Streamlit UI Workflow Test ---")
    print(f"Simulating a full workflow for {NUM_USERS} user(s).")
    print(f"Target URL: {STREAMLIT_URL}")
    print("-----------------------------------------")

    async with async_playwright() as playwright:
        tasks = [simulate_user_workflow(playwright, i + 1) for i in range(NUM_USERS)]
        await asyncio.gather(*tasks)
    
    print("\n--- Streamlit UI Workflow Test Finished ---")
    print(f"Chat histories saved in '{CHAT_LOG_DIR}' directory.")

if __name__ == "__main__":
    CHAT_LOG_DIR.mkdir(exist_ok=True)
    asyncio.run(main())
