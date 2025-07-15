import requests
import getpass
from requests.auth import HTTPBasicAuth

BASE_URL = "http://127.0.0.1:8000"
# BASE_URL = "http://40.82.161.202:8000"

def user_login():
    print("=== User Login ===")
    while True:
        username = input("Username: ").strip()
        password = getpass.getpass("Password: ")
        res = requests.get(f"{BASE_URL}/user/auth/check", auth=HTTPBasicAuth(username, password))
        if res.status_code == 200 and res.json().get("success"):
            print("✅ User authentication successful!\n")
            return username, password
        else:
            print("❌ Incorrect user credentials. Please try again.\n")

def print_history(auth):
    history_api = f"{BASE_URL}/user/chat/history"
    try:
        res = requests.get(history_api, auth=auth)
        print("*" * 10)
        if res.status_code == 200:
            history = res.json().get("history", [])
            print("\n--- User Message History ---")
            for i, msg in enumerate(history, 1):
                print(f"{i}: {msg}")
            print("----------------------------\n")
        else:
            print("Failed to fetch history.")
    except Exception as e:
        print(f"Error fetching history: {e}")

def chat():
    username, password = user_login()
    auth = HTTPBasicAuth(username, password)
    chat_api = f"{BASE_URL}/user/chat"
    while True:
        msg = input("You: ")
        if msg.lower() in ("exit", "quit"): break
        res = requests.post(chat_api, json={"user_id": username, "message": msg}, auth=auth)
        print_history(auth)
        if res.status_code == 200:
            print("Prompt: ", res.json().get("prompt"))
            print("*" * 10)
            print("🤖 Predict:", res.json().get("response"))
        else:
            print("Error:", res.text)

if __name__ == "__main__":
    chat()