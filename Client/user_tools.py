import getpass
import requests
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
        try:
            res = requests.post(f"{BASE_URL}/user/pdf/upload", params={"userid": self.username}, files=files, auth=self.auth)
            for _, file_tuple in files:
                file_tuple[1].close()
            print(res.json())
        except Exception as e:
            print(f"Error: {e}")

    def list_my_pdfs(self):
        try:
            res = requests.get(f"{BASE_URL}/user/pdf/list/{self.username}", auth=self.auth)
            pdfs = res.json().get("pdfs", [])
            if pdfs:
                print("Your uploaded PDFs:")
                for i, pdf in enumerate(pdfs, 1):
                    print(f"{i}. {pdf['filename']}")
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
            res = requests.post(f"{BASE_URL}/pdf/ingest/{filename}", auth=self.auth)
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
        filename = input("Enter PDF filename to remove from data: ").strip()
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
            print("    9. Exit")
            choice = input("Select an option (1-9): ").strip()
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