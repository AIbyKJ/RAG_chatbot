import requests

API = "http://40.82.161.202:8000/chat"
def print_history(user_id):
    history_api = f"http://40.82.161.202:8000/history/{user_id}"
    try:
        res = requests.get(history_api)
        print("ahsdflkhaskjld")
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
    user_id = "user6"
    while True:
        msg = input("You: ")
        if msg.lower() in ("exit", "quit"): break
        res = requests.post(API, json={"user_id": user_id, "message": msg})
        print_history(user_id)

        print("Prompt: ", res.json()["prompt"])
        print("*" * 10)
        print("🤖 Predict:", res.json()["response"])



if __name__ == "__main__":
    chat()