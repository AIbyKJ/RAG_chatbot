import getpass
import requests
from requests.auth import HTTPBasicAuth

BASE_URL = "http://127.0.0.1:8000"
# BASE_URL = "http://40.82.161.202:8000"

def admin_login():
    print("=== Admin Login ===")
    while True:
        username = input("Admin Username: ").strip()
        password = getpass.getpass("Admin Password: ")
        res = requests.get(f"{BASE_URL}/admin/auth/check", auth=HTTPBasicAuth(username, password))
        if res.status_code == 200 and res.json().get("success"):
            print("✅ Admin authentication successful!\n")
            return username, password
        else:
            print("❌ Incorrect admin credentials. Please try again.\n")

def user_management_menu(auth):
    while True:
        print("\n=== User Management ===")
        print("    1. List users")
        print("    2. Add user")
        print("    3. Delete user")
        print("    4. Reset user password")
        print("    5. Back")
        choice = input("Select an option (1-5): ").strip()
        if choice == "1":
            res = requests.get(f"{BASE_URL}/admin/users", auth=auth)
            print(res.json())
        elif choice == "2":
            username = input("New username: ").strip()
            password = getpass.getpass("New password: ")
            res = requests.post(f"{BASE_URL}/admin/users", json={"username": username, "password": password}, auth=auth)
            print(res.json())
        elif choice == "3":
            username = input("Username to delete: ").strip()
            res = requests.delete(f"{BASE_URL}/admin/users/{username}", auth=auth)
            print(res.json())
        elif choice == "4":
            username = input("Username to reset: ").strip()
            password = getpass.getpass("New password: ")
            res = requests.post(f"{BASE_URL}/admin/users/{username}/reset_password", json={"password": password}, auth=auth)
            print(res.json())
        elif choice == "5":
            break
        else:
            print("Invalid choice.")

def chat_management_menu(auth):
    while True:
        print("\n=== Chat Management ===")
        print("    1. Get chat history by user ID")
        print("    2. Clear all users' chat history")
        print("    3. Clear chat history by user ID")
        print("    4. Back")
        choice = input("Select an option (1-4): ").strip()
        if choice == "1":
            user_id = input("User ID: ").strip()
            res = requests.get(f"{BASE_URL}/admin/chat/history/{user_id}", auth=auth)
            print(res.json())
        elif choice == "2":
            res = requests.delete(f"{BASE_URL}/admin/vectordb/memory", auth=auth)
            print(res.json())
        elif choice == "3":
            user_id = input("User ID: ").strip()
            res = requests.delete(f"{BASE_URL}/admin/vectordb/memory/{user_id}", auth=auth)
            print(res.json())
        elif choice == "4":
            break
        else:
            print("Invalid choice.")

def data_management_menu(auth):
    while True:
        print("\n=== Data Management ===")
        print("    1. Upload all PDFs in a folder (public)")
        print("    2. Upload all PDFs in a folder (to user)")
        print("    3. Upload PDF (public)")
        print("    4. Upload PDF (to user)")
        print("    5. Delete PDF by filename")
        print("    6. Delete PDFs by user")
        print("    7. Delete all PDFs (public)")
        print("    8. Delete all PDFs (for user)")
        print("    9. List all PDFs")
        print("   10. Back")
        choice = input("Select an option (1-10): ").strip()
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
            res = requests.post(f"{BASE_URL}/admin/pdf/upload", files=files, auth=auth)
            for _, file_tuple in files:
                file_tuple[1].close()
            print(res.json())
        elif choice == "2":
            folder_path = input("Folder path: ").strip()
            user = input("User ID: ").strip()
            import os
            files = []
            for f in os.listdir(folder_path):
                if f.lower().endswith('.pdf'):
                    files.append(("files", (f, open(os.path.join(folder_path, f), "rb"), "application/pdf")))
            if not files:
                print("No PDF files found in the folder.")
                continue
            res = requests.post(f"{BASE_URL}/admin/pdf/upload?owner={user}", files=files, auth=auth)
            for _, file_tuple in files:
                file_tuple[1].close()
            print(res.json())
        elif choice == "3":
            path = input("PDF path: ").strip()
            files = {"files": (path.split("/")[-1], open(path, "rb"), "application/pdf")}
            res = requests.post(f"{BASE_URL}/admin/pdf/upload", files=files, auth=auth)
            print(res.json())
        elif choice == "4":
            path = input("PDF path: ").strip()
            user = input("User ID: ").strip()
            files = {"files": (path.split("/")[-1], open(path, "rb"), "application/pdf")}
            res = requests.post(f"{BASE_URL}/admin/pdf/upload?owner={user}", files=files, auth=auth)
            print(res.json())
        elif choice == "5":
            filename = input("Filename: ").strip()
            res = requests.delete(f"{BASE_URL}/admin/pdf/{filename}", auth=auth)
            print(res.json())
        elif choice == "6":
            user = input("User ID: ").strip()
            res = requests.delete(f"{BASE_URL}/admin/pdf/user/{user}", auth=auth)
            print(res.json())
        elif choice == "7":
            res = requests.delete(f"{BASE_URL}/admin/pdf", auth=auth)
            print(res.json())
        elif choice == "8":
            user = input("User ID: ").strip()
            res = requests.delete(f"{BASE_URL}/admin/pdf/user/{user}", auth=auth)
            print(res.json())
        elif choice == "9":
            res = requests.get(f"{BASE_URL}/admin/pdf", auth=auth)
            print(res.json())
        elif choice == "10":
            break
        else:
            print("Invalid choice.")

def vectordb_management_menu(auth):
    while True:
        print("\n=== VectorDB Management ===")
        print("    1. Ingest all PDFs (public)")
        print("    2. Ingest PDF by filename")
        print("    3. Remove PDF data by filename")
        print("    4. Remove PDF data by user")
        print("    5. Remove all PDF data from vectordb")
        print("    6. List available PDF data")
        print("    7. Back")
        choice = input("Select an option (1-7): ").strip()
        if choice == "1":
            res = requests.post(f"{BASE_URL}/admin/vectordb/ingest/all", auth=auth)
            print(res.json())
        elif choice == "2":
            filename = input("Filename: ").strip()
            res = requests.post(f"{BASE_URL}/admin/vectordb/ingest/{filename}", auth=auth)
            print(res.json())
        elif choice == "3":
            filename = input("Filename: ").strip()
            res = requests.delete(f"{BASE_URL}/admin/vectordb/pdf/{filename}", auth=auth)
            print(res.json())
        elif choice == "4":
            user = input("User ID: ").strip()
            res = requests.delete(f"{BASE_URL}/admin/vectordb/pdf/user/{user}", auth=auth)
            print(res.json())
        elif choice == "5":
            res = requests.delete(f"{BASE_URL}/admin/vectordb/pdf", auth=auth)
            print(res.json())
        elif choice == "6":
            res = requests.get(f"{BASE_URL}/admin/vectordb/pdf", auth=auth)
            print(res.json())
        elif choice == "7":
            break
        else:
            print("Invalid choice.")

def main():
    username, password = admin_login()
    auth = HTTPBasicAuth(username, password)
    while True:
        print("\n=== Admin Tools ===")
        print("    1. User Management")
        print("    2. Chat Management")
        print("    3. Data Management")
        print("    4. VectorDB Management")
        print("    5. Exit")
        choice = input("Select an option (1-5): ").strip()
        if choice == "1":
            user_management_menu(auth)
        elif choice == "2":
            chat_management_menu(auth)
        elif choice == "3":
            data_management_menu(auth)
        elif choice == "4":
            vectordb_management_menu(auth)
        elif choice == "5":
            print("Exiting...")
            break
        else:
            print("Invalid choice.")

if __name__ == "__main__":
    main() 
