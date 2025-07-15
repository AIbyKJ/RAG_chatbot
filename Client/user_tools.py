import getpass
import requests
from requests.auth import HTTPBasicAuth

BASE_URL = "http://127.0.0.1:8000"

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

def chat_menu(auth, username):
    print("\n=== Chat ===")
    while True:
        msg = input("You: ")
        if msg.lower() in ("exit", "quit"): break
        res = requests.post(f"{BASE_URL}/user/chat", json={"user_id": username, "message": msg}, auth=auth)
        if res.status_code == 200:
            print("Prompt:", res.json().get("prompt"))
            print("🤖 Predict:", res.json().get("response"))
        else:
            print("Error:", res.text)

def data_management_menu(auth, username):
    while True:
        print("\n=== Data Management ===")
        print("    1. Upload all PDFs in a folder")
        print("    2. Upload PDF by filename")
        print("    3. Delete all my PDFs")
        print("    4. Delete PDF by filename")
        print("    5. List my PDFs")
        print("    6. Back")
        choice = input("Select an option (1-6): ").strip()
        if choice == "1":
            folder_path = input("Folder path: ").strip()
            import os
            files = []
            for f in os.listdir(folder_path):
                if f.lower().endswith('.pdf'):
                    files.append(("files", (f, open(os.path.join(folder_path, f), "rb"), "application/pdf")))
            if not files:
                print("No PDF files found in the folder.")
                continue
            res = requests.post(f"{BASE_URL}/user/pdf/upload", files=files, auth=auth)
            for _, file_tuple in files:
                file_tuple[1].close()
            print(res.json())
        elif choice == "2":
            path = input("PDF path: ").strip()
            files = {"files": (path.split("/")[-1], open(path, "rb"), "application/pdf")}
            res = requests.post(f"{BASE_URL}/user/pdf/upload", files=files, auth=auth)
            print(res.json())
        elif choice == "3":
            res = requests.delete(f"{BASE_URL}/user/pdf", auth=auth)
            print(res.json())
        elif choice == "4":
            filename = input("Filename: ").strip()
            res = requests.delete(f"{BASE_URL}/user/pdf/{filename}", auth=auth)
            print(res.json())
        elif choice == "5":
            res = requests.get(f"{BASE_URL}/user/pdf", auth=auth)
            print(res.json())
        elif choice == "6":
            break
        else:
            print("Invalid choice.")

def vectordb_management_menu(auth, username):
    while True:
        print("\n=== VectorDB Management ===")
        print("    1. Ingest all PDFs (mine and public)")
        print("    2. Ingest PDF by filename")
        print("    3. Remove PDF data by filename")
        print("    4. Remove all my PDF data from vectordb")
        print("    5. List my PDF data")
        print("    6. Back")
        choice = input("Select an option (1-6): ").strip()
        if choice == "1":
            res = requests.post(f"{BASE_URL}/user/vectordb/ingest/all", auth=auth)
            print(res.json())
        elif choice == "2":
            filename = input("Filename: ").strip()
            res = requests.post(f"{BASE_URL}/user/vectordb/ingest/{filename}", auth=auth)
            print(res.json())
        elif choice == "3":
            filename = input("Filename: ").strip()
            res = requests.delete(f"{BASE_URL}/user/vectordb/pdf/{filename}", auth=auth)
            print(res.json())
        elif choice == "4":
            res = requests.delete(f"{BASE_URL}/user/vectordb/pdf/all", auth=auth)
            print(res.json())
        elif choice == "5":
            res = requests.get(f"{BASE_URL}/user/vectordb/pdf", auth=auth)
            print(res.json())
        elif choice == "6":
            break
        else:
            print("Invalid choice.")

def main():
    username, password = user_login()
    auth = HTTPBasicAuth(username, password)
    while True:
        print("\n=== User Tools ===")
        print("    1. Chat")
        print("    2. Data Management")
        print("    3. VectorDB Management")
        print("    4. Exit")
        choice = input("Select an option (1-4): ").strip()
        if choice == "1":
            chat_menu(auth, username)
        elif choice == "2":
            data_management_menu(auth, username)
        elif choice == "3":
            vectordb_management_menu(auth, username)
        elif choice == "4":
            print("Exiting...")
            break
        else:
            print("Invalid choice.")

if __name__ == "__main__":
    main() 