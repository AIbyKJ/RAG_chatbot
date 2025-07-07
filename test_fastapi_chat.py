import pytest
import asyncio
import httpx
import time
from datetime import datetime
import random

n_requests = 100
test_duration = 120

@pytest.fixture
def log_to_file(request):
    return request.config.getoption("--log-to-file")

@pytest.fixture
def log_to_prompt(request):
    return request.config.getoption("--log-to-prompt")

question_list = [
    "Who is Elara?",
    "Who is Barnaby?",
    "My name is Sander",
    "What is my name?",
    "Where Elara lives?"
]

@pytest.mark.asyncio
async def test_server_100_requests_per_minute(log_to_prompt, log_to_file):

    users = [f"user_{i % 5}" for i in range(n_requests)]
    interval = test_duration / n_requests  # evenly spread over 2 minutes

    success_count = {"count": 0}
    lock = asyncio.Lock()

    async def send_chat(index, user_id, delay):
        await asyncio.sleep(delay)
        message = f"{random.choice(question_list)} {index}"
        try:
            async with httpx.AsyncClient(timeout=20.0) as ac:
                response = await ac.post(
                    "http://40.82.161.202:8000/chat",
                    json={"user_id": user_id, "message": message}
                )
                assert response.status_code == 200
                json_data = response.json()
                assert "response" in json_data
                async with lock:
                    success_count["count"] += 1

                await asyncio.sleep(1)
                now = datetime.now()
                # Fetch user message history from the server
                history_response = await ac.get(f"http://40.82.161.202:8000/history/{user_id}")
                history = history_response.json().get("history", [])
                print("TEST:", history)
                log_line = (
                    f"{'*' * 30}\n"
                    f"Time: {now.strftime('%Y-%m-%d %H:%M:%S')}\n"
                    f"Request #{index + 1}/{n_requests}\n"
                    f"User: {user_id}\n"
                    f"Message: {message}\n"
                    f"Response: {json_data['response']}\n"
                    f"Prompt: {json_data.get('prompt', 'N/A')}\n"
                    f"Full History: {history}\n"
                    f"{'*' * 30}\n"
                )
                if log_to_prompt:
                    print(log_line)
                if log_to_file:
                    with open("test_log.txt", "a", encoding="utf-8") as f:
                        f.write(log_line + "\n")
                return json_data["response"]
        except Exception as e:
            error_log = f"[ERROR] Request #{index + 1} failed: {e}\n"
            print(error_log)
            with open("test_log.txt", "a", encoding="utf-8") as f:
                f.write(error_log + "\n")
            return None
    start_time = time.time()
    response_times = []
    async def timed_send_chat(index, user_id, delay):
        t0 = time.time()
        result = await send_chat(index, user_id, delay)
        t1 = time.time()
        response_times.append(t1 - t0)
        return result
    tasks = [
        timed_send_chat(i, users[i], i * interval)
        for i in range(n_requests)
    ]
    results = await asyncio.gather(*tasks)
    elapsed = time.time() - start_time
    passed = success_count["count"]
    failed = n_requests - passed
    avg_response_time = sum(response_times) / len(response_times) if response_times else 0
    summary = (
        f"\n✅ {passed} / {n_requests} requests succeeded.\n"
        f"❌ {failed} requests failed.\n"
        f"🕒 Total time elapsed: {elapsed:.2f} seconds\n"
        f"⏱️ Average response time: {avg_response_time:.2f} seconds\n"
    )
    if log_to_prompt:
        print(summary)
    if log_to_file:
        with open("test_log.txt", "a", encoding="utf-8") as f:
            f.write(summary + "\n")
    assert failed <= 5
    assert elapsed >= test_duration
