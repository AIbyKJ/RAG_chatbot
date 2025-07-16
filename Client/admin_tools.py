import getpass
import requests
from requests.auth import HTTPBasicAuth

BASE_URL = "http://127.0.0.1:8000"

def admin_login():
    print("=== Admin Login ===")
    while True:
        username = input("Admin username: ").strip()
        password = getpass.getpass("Password: ")
        try:
            res = requests.get(f"{BASE_URL}/admin/auth/check", auth=HTTPBasicAuth(username, password))
            if res.status_code == 200:
                print("✅ Admin authentication successful!\n")
                return username, password
            else:
                print("❌ Incorrect admin credentials. Please try again.\n")
        except Exception as e:
            print(f"❌ Error connecting to server: {e}\n")

def user_management_menu(auth):
    while True:
        print("\n--- User Management ---")
        print("1. List users")
        print("2. Add user")
        print("3. Delete user")
        print("4. Reset user password")
        print("0. Back to main menu")
        choice = input("Select option: ").strip()
        if choice == "1":
            res = requests.get(f"{BASE_URL}/admin/users", auth=auth)
            print("\nUsers:")
            for u in res.json():
                print(f"- {u['id']}: {u['username']}")
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
            username = input("Username to reset password: ").strip()
            password = getpass.getpass("New password: ")
            res = requests.post(f"{BASE_URL}/admin/users/{username}/reset_password", json={"password": password}, auth=auth)
            print(res.json())
        elif choice == "0":
            break
        else:
            print("Invalid option.")

def chat_management_menu(auth):
    while True:
        print("\n--- Chat Management ---")
        print("1. View user chat history")
        print("0. Back to main menu")
        choice = input("Select option: ").strip()
        if choice == "1":
            user_id = input("User ID: ").strip()
            res = requests.get(f"{BASE_URL}/admin/chat/history/{user_id}", auth=auth)
            data = res.json()
            print(f"\nChat history for {user_id}:")
            for i, msg in enumerate(data.get("history", []), 1):
                print(f"{i}: {msg}")
        elif choice == "0":
            break
        else:
            print("Invalid option.")

def data_management_menu(auth):
    while True:
        print("\n--- Data Management ---")
        print("1. Upload PDF(s)")
        print("2. Upload all PDFs from folder")
        print("3. List all PDFs")
        print("4. Delete PDF(s)")
        print("5. Delete all public PDFs")
        print("0. Back to main menu")
        choice = input("Select option: ").strip()
        if choice == "1":
            filepaths = input("Enter PDF file paths (comma separated): ").split(",")
            files = [("files", (fp.strip(), open(fp.strip(), "rb"), "application/pdf")) for fp in filepaths if fp.strip()]
            is_public = input("Is public? (1 for yes, 0 for no): ").strip()
            res = requests.post(f"{BASE_URL}/admin/pdf/upload", files=files, data={"is_public": is_public}, auth=auth)
            print(res.json())
        elif choice == "2":
            folder = input("Enter folder path: ").strip()
            files = []
            import os
            for fname in os.listdir(folder):
                if fname.lower().endswith(".pdf"):
                    files.append(("files", (fname, open(os.path.join(folder, fname), "rb"), "application/pdf")))
            is_public = input("Is public? (1 for yes, 0 for no): ").strip()
            res = requests.post(f"{BASE_URL}/admin/pdf/upload", files=files, data={"is_public": is_public}, auth=auth)
            print(res.json())
        elif choice == "3":
            res = requests.get(f"{BASE_URL}/admin/pdf", auth=auth)
            print(res.json())
        elif choice == "4":
            filenames = input("Enter filenames to delete (comma separated): ").split(",")
            res = requests.post(f"{BASE_URL}/admin/pdf/delete", json={"filenames": [f.strip() for f in filenames]}, auth=auth)
            print(res.json())
        elif choice == "5":
            res = requests.post(f"{BASE_URL}/admin/pdf/delete_public", auth=auth)
            print(res.json())
        elif choice == "0":
            break
        else:
            print("Invalid option.")

def vectordb_management_menu(auth):
    while True:
        print("\n--- VectorDB Management ---")
        print("1. Ingest all public PDFs")
        print("2. Ingest PDF by filename (public or specific user)")
        print("3. Remove PDF data by filename")
        print("4. Remove PDF data by user")
        print("5. List available PDF data")
        print("6. Clear all users' memory")
        print("7. Clear user memory by user ID")
        print("0. Back to main menu")
        choice = input("Select option: ").strip()
        if choice == "1":
            res = requests.post(f"{BASE_URL}/admin/vectordb/ingest/all", auth=auth)
            print(res.json())
        elif choice == "2":
            filename = input("Filename: ").strip()
            print("Ingest as:")
            print("1. Public")
            print("2. Specific user")
            ingest_choice = input("Select option: ").strip()
            if ingest_choice == "1":
                res = requests.post(f"{BASE_URL}/admin/vectordb/ingest/public/{filename}", auth=auth)
                print(res.json())
            elif ingest_choice == "2":
                user_id = input("User ID: ").strip()
                res = requests.post(f"{BASE_URL}/admin/vectordb/ingest/private/{filename}?user_id={user_id}", auth=auth)
                print(res.json())
            else:
                print("Invalid option.")
        elif choice == "3":
            filename = input("Filename: ").strip()
            res = requests.delete(f"{BASE_URL}/admin/vectordb/pdf/{filename}", auth=auth)
            print(res.json())
        elif choice == "4":
            owner = input("User ID: ").strip()
            res = requests.delete(f"{BASE_URL}/admin/vectordb/pdf/user/{owner}", auth=auth)
            print(res.json())
        elif choice == "5":
            res = requests.get(f"{BASE_URL}/admin/vectordb/pdf", auth=auth)
            print(res.json())
        elif choice == "6":
            res = requests.delete(f"{BASE_URL}/admin/vectordb/memory", auth=auth)
            print(res.json())
        elif choice == "7":
            user_id = input("User ID: ").strip()
            res = requests.delete(f"{BASE_URL}/admin/vectordb/memory/{user_id}", auth=auth)
            print(res.json())
        elif choice == "0":
            break
        else:
            print("Invalid option.")

def main():
    username, password = admin_login()
    auth = HTTPBasicAuth(username, password)
    while True:
        print("\n=== Admin Main Menu ===")
        print("1. User Management")
        print("2. Chat Management")
        print("3. Data Management")
        print("4. VectorDB Management")
        print("0. Exit")
        choice = input("Select option: ").strip()
        if choice == "1":
            user_management_menu(auth)
        elif choice == "2":
            chat_management_menu(auth)
        elif choice == "3":
            data_management_menu(auth)
        elif choice == "4":
            vectordb_management_menu(auth)
        elif choice == "0":
            print("Goodbye!")
            break
        else:
            print("Invalid option.")

if __name__ == "__main__":
    main() 
