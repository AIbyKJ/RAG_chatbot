import requests

# BASE_URL = "http://127.0.0.1:8000"
BASE_URL = "http://40.82.161.202:8000"

def print_history(user_id):
    history_api = f"{BASE_URL}/chat/history/{user_id}"
    try:
        res = requests.get(history_api)
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
    chat_api = f"{BASE_URL}/chat"

    user_id = "user_6"
    while True:
        msg = input("You: ")
        if msg.lower() in ("exit", "quit"): break
        res = requests.post(chat_api, json={"user_id": user_id, "message": msg})
        print_history(user_id)

        print("Prompt: ", res.json()["prompt"])
        print("*" * 10)
        print("🤖 Predict:", res.json()["response"])



if __name__ == "__main__":
    chat()