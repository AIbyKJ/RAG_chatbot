import requests

API = "http://127.0.0.1:8000/chat"

def chat():
    user_id = "user1"
    while True:
        msg = input("You: ")
        if msg.lower() in ("exit", "quit"): break
        res = requests.post(API, json={"user_id": user_id, "message": msg})
        print("🤖:", res.json()["response"])

if __name__ == "__main__":
    chat()