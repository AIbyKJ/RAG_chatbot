import getpass
import requests
<<<<<<< HEAD
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
=======
import os
from requests.auth import HTTPBasicAuth

BASE_URL = "http://127.0.0.1:8000"
# BASE_URL = "http://40.82.161.202:8000"

class UserToolsManager:
    def __init__(self, username, password):
        self.username = username
        self.password = password
        self.auth = HTTPBasicAuth(username, password)

    def upload_pdfs(self):
        pdf_paths = input("Enter PDF file paths to upload (comma separated): ").split(",")
        pdf_paths = [p.strip() for p in pdf_paths if p.strip()]
        files = [("files", (os.path.basename(path), open(path, "rb"), "application/pdf")) for path in pdf_paths if os.path.isfile(path)]
        if not files:
            print("No valid PDF files provided.")
            return
        is_public = input("Upload to public? (y/n): ").strip().lower() == 'y'
        try:
            if is_public:
                res = requests.post(f"{BASE_URL}/user/pdf/upload", params={"userid": self.username, "is_global": 1}, files=files, auth=self.auth)
            else:
                res = requests.post(f"{BASE_URL}/user/pdf/upload", params={"userid": self.username, "is_global": 0}, files=files, auth=self.auth)
            for _, file_tuple in files:
                file_tuple[1].close()
            result = res.json()
            print(result.get("message", result))
            if result.get("skipped"):
                print("Some files were skipped:")
                for entry in result["skipped"]:
                    print(f"  {entry['filename']}: {entry['reason']}")
        except Exception as e:
            print(f"Error: {e}")

    def upload_all_pdfs_from_folder(self):
        folder = input("Enter folder path containing PDFs: ").strip()
        if not os.path.isdir(folder):
            print("Invalid folder path.")
            return
        pdf_paths = [os.path.join(folder, f) for f in os.listdir(folder) if f.lower().endswith('.pdf')]
        if not pdf_paths:
            print("No PDF files found in the folder.")
            return
        files = [("files", (os.path.basename(path), open(path, "rb"), "application/pdf")) for path in pdf_paths]
        is_public = input("Upload to public? (y/n): ").strip().lower() == 'y'
        try:
            if is_public:
                res = requests.post(f"{BASE_URL}/user/pdf/upload", params={"userid": self.username, "is_global": 1}, files=files, auth=self.auth)
            else:
                res = requests.post(f"{BASE_URL}/user/pdf/upload", params={"userid": self.username, "is_global": 0}, files=files, auth=self.auth)
            for _, file_tuple in files:
                file_tuple[1].close()
            result = res.json()
            print(result.get("message", result))
            if result.get("skipped"):
                print("Some files were skipped:")
                for entry in result["skipped"]:
                    print(f"  {entry['filename']}: {entry['reason']}")
        except Exception as e:
            print(f"Error: {e}")

    def list_my_pdfs(self):
        try:
            res = requests.get(f"{BASE_URL}/user/pdf/list/{self.username}", auth=self.auth)
            pdfs = res.json().get("pdfs", [])
            if pdfs:
                print("Your uploaded PDFs (relative paths):")
                for i, pdf in enumerate(pdfs, 1):
                    print(f"{i}. {pdf}")
            else:
                print("No PDFs found.")
        except Exception as e:
            print(f"Error: {e}")

    def ingest_my_pdf(self):
        try:
            res = requests.get(f"{BASE_URL}/user/pdf/list/{self.username}", auth=self.auth)
            pdfs = res.json().get("pdfs", [])
            if not pdfs:
                print("No PDFs to ingest.")
                return
            print("Your uploaded PDFs:")
            for i, pdf in enumerate(pdfs, 1):
                print(f"{i}. {pdf['filename']}")
            idx = input("Enter the number of the PDF to ingest: ").strip()
            try:
                idx = int(idx) - 1
                filename = pdfs[idx]['filename']
            except Exception:
                print("Invalid selection.")
                return
            # Use the user ingestion endpoint
            res = requests.post(f"{BASE_URL}/user/pdf/ingest/{filename}", auth=self.auth)
            print(res.json())
        except Exception as e:
            print(f"Error: {e}")

    def change_password(self):
        current_pw = getpass.getpass("Enter your current password: ")
        new_pw = getpass.getpass("Enter new password: ")
        confirm_pw = getpass.getpass("Confirm new password: ")
        if new_pw != confirm_pw:
            print("Passwords do not match.")
            return
        try:
            res = requests.post(
                f"{BASE_URL}/user/change_password",
                json={
                    "userid": self.username,
                    "current_password": current_pw,
                    "new_password": new_pw
                },
                auth=self.auth
            )
            if res.status_code == 200 and res.json().get("message") == "Password changed successfully.":
                print("Password changed successfully.")
                self.password = new_pw  # Update local password for session
            else:
                print("Password change failed:", res.json().get("error", res.text))
        except Exception as e:
            print(f"Error: {e}")

    def delete_my_pdf_from_chroma_by_filename(self):
        filename = input("Enter PDF filename to remove from Chroma: ").strip()
        res = requests.delete(f"{BASE_URL}/vectordb/pdf/{filename}", auth=self.auth)
        print(res.json())

    def delete_all_my_pdfs_from_chroma(self):
        res = requests.delete(f"{BASE_URL}/vectordb/pdf/user/me", auth=self.auth)
        print(res.json())

    def delete_my_pdf_from_data_by_filename(self):
        filename = input("Enter PDF relative path to remove from data (e.g., u1/LHahn.pdf or public/LHahn.pdf): ").strip()
        res = requests.delete(f"{BASE_URL}/pdf/{filename}", auth=self.auth)
        print(res.json())

    def delete_all_my_pdfs_from_data(self):
        res = requests.delete(f"{BASE_URL}/pdf/user/me", auth=self.auth)
        print(res.json())

    def main_menu(self):
        while True:
            print("\n=== User Tools CLI ===")
            print("    1. Upload my PDFs")
            print("    2. List my PDFs")
            print("    3. Ingest my PDF")
            print("    4. Change my password")
            print("    5. Delete my PDF from Chroma by filename")
            print("    6. Delete all my PDFs from Chroma")
            print("    7. Delete my PDF from data by filename")
            print("    8. Delete all my PDFs from data")
            print("    9. Upload ALL PDFs from folder")
            print("   10. Exit")
            choice = input("Select an option (1-10): ").strip()
            if choice == "1":
                self.upload_pdfs()
            elif choice == "2":
                self.list_my_pdfs()
            elif choice == "3":
                self.ingest_my_pdf()
            elif choice == "4":
                self.change_password()
            elif choice == "5":
                self.delete_my_pdf_from_chroma_by_filename()
            elif choice == "6":
                self.delete_all_my_pdfs_from_chroma()
            elif choice == "7":
                self.delete_my_pdf_from_data_by_filename()
            elif choice == "8":
                self.delete_all_my_pdfs_from_data()
            elif choice == "9":
                self.upload_all_pdfs_from_folder()
            elif choice == "10":
                print("Exiting...")
                break
            else:
                print("Invalid choice.")

def authenticate():
    print("=== User Login Required ===")
    while True:
        username = input("Username: ").strip()
        password = getpass.getpass("Password: ")
        try:
            res = requests.get(f"{BASE_URL}/auth/check", auth=HTTPBasicAuth(username, password))
            if res.status_code == 200 and res.json().get("success"):
                print("✅ Authentication successful!\n")
                return username, password
            else:
                print("❌ Incorrect username or password. Please try again.\n")
        except Exception as e:
            print(f"❌ Error connecting to server: {e}\n")

if __name__ == "__main__":
    username, password = authenticate()
    tools = UserToolsManager(username, password)
    tools.main_menu() 
>>>>>>> 3578a32f7d0fa3879920ea6a704e04ffd97717f7
