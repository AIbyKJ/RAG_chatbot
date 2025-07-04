import requests

API = "http://127.0.0.1:8000/chat"
def clear_memory_by_user():
    user_id = input("Enter user ID to clear memory: ").strip()
    if not user_id:
        print("User ID cannot be empty.")
        return
    res = requests.delete(f"http://127.0.0.1:8000/memory/{user_id}")
    if res.status_code == 200:
        print(res.json().get("message", "Memory cleared."))
    else:
        print("Error:", res.json().get("error", "Failed to clear memory."))

def clear_all_memory():
    res = requests.delete("http://127.0.0.1:8000/memory")
    if res.status_code == 200:
        print(res.json().get("message", "All memory cleared."))
    else:
        print("Error:", res.json().get("error", "Failed to clear all memory."))

if __name__ == "__main__":
    clear_all_memory()