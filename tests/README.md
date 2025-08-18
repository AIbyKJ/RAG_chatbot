
# Frontend Service

This directory contains the UI for the RAG Chatbot Portal, available in both Gradio and Streamlit.

## 1\. Local Setup

First, set up your local environment and connect it to the backend.

1.  **Create a Virtual Environment & Install Dependencies**:

    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    pip install -r requirements.txt
    ```

2.  **Set Backend URL**: The UI needs to know where the backend is running.

    ```bash
    export BACKEND_URL="http://127.0.0.1:8000"
    ```

## 2\. Running the Applications

Make sure your backend service is running, then choose which UI to start.

### Gradio

```bash
python UI_Gradio.py
```

> Access it at: `http://localhost:7860`

### Streamlit

```bash
streamlit run Home.py
```

> Access it at: `http://localhost:8501`

-----

## 3\. UI Automation Testing

End-to-end tests are available for both UIs using **Playwright**. These tests simulate a full user workflow: login, PDF upload, data ingestion, and a chat session.

### One-Time Test Setup

Complete these steps once before running either test.

1.  **Install Playwright**:

    ```bash
    pip install playwright
    playwright install
    ```

2.  **Create Test Users**: The scripts require users named `testuser1`, `testuser2`, etc., with the password `password`. Create them using the Admin dashboard of either running UI.

3.  **Prepare Test Data**: The tests need PDF files to upload. Create the following directory structure:

    ```
    .
    ├── data_user1_pdfs/
    │   └── file1.pdf
    ├── data_user2_pdfs/
    │   └── file2.pdf
    └── ... (and so on)
    ```

### Running the Tests

Ensure the backend and the specific frontend you want to test are running.

#### ► To Test the Gradio UI:

```bash
export GRADIO_URL="http://127.0.0.1:7860"
python test_gradio_workflow.py
```

#### ► To Test the Streamlit UI:

```bash
export STREAMLIT_URL="http://127.0.0.1:8501"
python test_streamlit_workflow.py
```

### Test Output

  - Progress will be displayed in your terminal.
  - Full chat histories are saved in the `./chat_logs/` directory.
  - If a test fails, a screenshot (`failure_...png`) is saved for debugging.