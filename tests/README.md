# Load Testing

This directory contains scripts to perform load testing on the RAG Chatbot application.

Two types of tests are provided:

1. Backend API Test (`locustfile.py`): Directly tests the performance of the FastAPI backend endpoints using Locust.

2. Frontend UI Test (`frontend_test_playwrite.py`): Simulates real users interacting with the Streamlit frontend in a browser to test the end-to-end user experience using Playwright.

## 1. Backend API Load Test

This test sends direct requests to the backend API to measure its raw performance.

### How to Run

1. Install Dependencies:

    `pip install locust reportlab`

2. Prepare Environment: Run `python setup_test_environment.py` to create test users and files. Your backend must be running for this step.

3. Start Test:

    `locust -f locustfile.py`

4. Configure Swarm: Open `http://localhost:8089`, set the number of users, and set the Host to your backend URL (e.g., `http://localhost:8000`).

## 2. Frontend UI Load Test (Integration Test)
This test uses Playwright to launch and control 20 headless browsers in parallel, simulating real users interacting with the Streamlit UI. It measures the end-to-end response time from a user's perspective.

### How to Run
#### Step 1: Install Dependencies
This test requires additional dependencies.

    `pip install playwright reportlab`

    `playwright install chromium`

#### Step 2: Prepare the Environment
Ensure the backend and frontend services are running (e.g., via `docker-compose up`). Then, run the setup script to create the necessary test users.

`python setup_test_environment.py`

#### Step 3: Run the Test Locally
From the `tests/` directory, execute the standalone test script.

`python frontend_test_playwrite.py`

The script will launch 20 browsers and run for the duration specified in the configuration. You will see detailed logs printed to your console. If any user session fails, a screenshot named `failure_user_X.png` will be saved for debugging.

#### Step 4: Run the Test from Different Geographic Locations (on GCP)
To simulate users from different countries, you can run the `standalone_ui_test.py` script on virtual machines in different GCP regions.

1. Setup Worker VMs: Create small `e2-medium` virtual machines in different GCP regions (e.g., `us-central1`, `europe-west1`, `asia-east1`).

2. On each VM:

    - Install Python.

    - Clone your project.

    - Install the test dependencies from Step 1.

    - Set the `FRONTEND_URL` environment variable to your public GCP frontend URL: `export FRONTEND_URL="https://your-public-frontend-url.a.run.app"`

    - Run the test: python `standalone_ui_test.py`

Monitor: You can monitor the logs from each VM and use GCP's Cloud Monitoring to observe the resource usage (CPU, RAM) of your deployed frontend and backend services during the test.