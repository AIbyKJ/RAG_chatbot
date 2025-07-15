import os
import requests
import getpass
from requests.auth import HTTPBasicAuth

class PDFDataManager:
    def __init__(self, username="", password="", base_url="http://127.0.0.1:8000"):
        self.username = username
        self.password = password
        self.base_url = base_url
        self.auth = HTTPBasicAuth(username, password)

    def upload_pdf_for_user(self):
        userid = input("Enter user ID to associate PDF with: ").strip()
        pdf_paths = input("Enter PDF file paths to upload (comma separated): ").split(",")
        pdf_paths = [p.strip() for p in pdf_paths if p.strip()]
        files = [("files", (os.path.basename(path), open(path, "rb"), "application/pdf")) for path in pdf_paths if os.path.isfile(path)]
        if not files:
            print("No valid PDF files provided.")
            return
        try:
            res = requests.post(f"{self.base_url}/admin/pdf/upload", params={"userid": userid, "is_global": 0}, files=files, auth=self.auth)
            for _, file_tuple in files:
                file_tuple[1].close()
            result = res.json()
            if "uploaded" in result:
                print(f"✅ Uploaded {len(result['uploaded'])} files: {result['uploaded']}")
            else:
                print(result)
        except Exception as e:
            print(f"Error: {e}")

    def upload_pdf_global(self):
        pdf_paths = input("Enter PDF file paths to upload (comma separated): ").split(",")
        pdf_paths = [p.strip() for p in pdf_paths if p.strip()]
        files = [("files", (os.path.basename(path), open(path, "rb"), "application/pdf")) for path in pdf_paths if os.path.isfile(path)]
        if not files:
            print("No valid PDF files provided.")
            return
        try:
            res = requests.post(f"{self.base_url}/admin/pdf/upload", params={"is_global": 1}, files=files, auth=self.auth)
            for _, file_tuple in files:
                file_tuple[1].close()
            result = res.json()
            if "uploaded" in result:
                print(f"✅ Uploaded {len(result['uploaded'])} files: {result['uploaded']}")
            else:
                print(result)
        except Exception as e:
            print(f"Error: {e}")

    def list_all_pdfs_with_users(self):
        try:
            res = requests.get(f"{self.base_url}/admin/pdf/list", auth=self.auth)
            pdfs = res.json().get("pdfs", [])
            if pdfs:
                print("PDFs with user associations:")
                for i, pdf in enumerate(pdfs, 1):
                    print(f"{i}. {pdf['filename']} (users: {pdf['users']}, is_global: {pdf['is_global']})")
            else:
                print("No PDFs found.")
        except Exception as e:
            print(f"Error: {e}")

    def remove_pdf_from_data_by_filename(self):
        filename = input("Enter PDF filename to remove from data: ").strip()
        res = requests.delete(f"{self.base_url}/pdf/{filename}", auth=self.auth)
        print(res.json())

    def remove_pdfs_from_data_by_userid(self):
        userid = input("Enter user ID to remove all their PDFs from data: ").strip()
        res = requests.delete(f"{self.base_url}/pdf/user/{userid}", auth=self.auth)
        result = res.json()
        if "message" in result:
            print(f"✅ {result['message']}")
            if "deleted_files" in result and result["deleted_files"]:
                print(f"   Files deleted: {result['deleted_files']}")
            if "deleted_from_db" in result and result["deleted_from_db"]:
                print(f"   Database records deleted: {result['deleted_from_db']}")
        else:
            print(result)

    def remove_all_pdfs_from_data(self):
        res = requests.delete(f"{self.base_url}/pdf", auth=self.auth)
        result = res.json()
        if "message" in result:
            print(f"✅ {result['message']}")
            if "deleted_files" in result and result["deleted_files"]:
                print(f"   Files deleted: {result['deleted_files']}")
            if "deleted_from_db" in result and result["deleted_from_db"]:
                print(f"   Database records deleted: {result['deleted_from_db']}")
        else:
            print(result)

    def ingest_pdfs_for_user(self):
        userid = input("Enter user ID to ingest PDFs for: ").strip()
        res = requests.post(f"{self.base_url}/pdf/ingest/user/{userid}", auth=self.auth)
        result = res.json()
        if "success" in result:
            if result["success"]:
                print(f"✅ Ingested {result.get('chunks', 0)} chunks from {len(result.get('ingested_files', []))} files for user {userid}")
            else:
                print(f"⚠️ {result.get('warning', 'Ingestion failed')}")
        else:
            print(f"❌ Error: {result.get('error', 'Unknown error')}")

    def ingest_pdf_for_user(self):
        userid = input("Enter user ID: ").strip()
        filename = input("Enter PDF filename to ingest: ").strip()
        res = requests.post(f"{self.base_url}/pdf/ingest/{filename}/user/{userid}", auth=self.auth)
        result = res.json()
        if "success" in result:
            if result["success"]:
                print(f"✅ Ingested {result.get('chunks', 0)} chunks from {result.get('ingested_file', filename)} for user {userid}")
            else:
                print(f"⚠️ {result.get('warning', 'Ingestion failed')}")
        else:
            print(f"❌ Error: {result.get('error', 'Unknown error')}")

    def upload_all_pdfs_from_folder_for_user(self):
        folder = input("Enter folder path containing PDFs: ").strip()
        userid = input("Enter user ID to associate PDFs with: ").strip()
        if not os.path.isdir(folder):
            print("Invalid folder path.")
            return
        pdf_paths = [os.path.join(folder, f) for f in os.listdir(folder) if f.lower().endswith('.pdf')]
        if not pdf_paths:
            print("No PDF files found in the folder.")
            return
        files = [("files", (os.path.basename(path), open(path, "rb"), "application/pdf")) for path in pdf_paths]
        try:
            res = requests.post(f"{self.base_url}/admin/pdf/upload", params={"userid": userid, "is_global": 0}, files=files, auth=self.auth)
            for _, file_tuple in files:
                file_tuple[1].close()
            result = res.json()
            if "uploaded" in result:
                print(f"✅ Uploaded {len(result['uploaded'])} files: {result['uploaded']}")
            else:
                print(result)
        except Exception as e:
            print(f"Error: {e}")

    def upload_all_pdfs_from_folder_global(self):
        folder = input("Enter folder path containing PDFs: ").strip()
        if not os.path.isdir(folder):
            print("Invalid folder path.")
            return
        pdf_paths = [os.path.join(folder, f) for f in os.listdir(folder) if f.lower().endswith('.pdf')]
        if not pdf_paths:
            print("No PDF files found in the folder.")
            return
        files = [("files", (os.path.basename(path), open(path, "rb"), "application/pdf")) for path in pdf_paths]
        try:
            res = requests.post(f"{self.base_url}/admin/pdf/upload", params={"is_global": 1}, files=files, auth=self.auth)
            for _, file_tuple in files:
                file_tuple[1].close()
            result = res.json()
            if "uploaded" in result:
                print(f"✅ Uploaded {len(result['uploaded'])} files: {result['uploaded']}")
            else:
                print(result)
        except Exception as e:
            print(f"Error: {e}")

    def remove_pdf_by_userid_and_filename(self):
        userid = input("Enter user ID: ").strip()
        filename = input("Enter PDF filename to remove: ").strip()
        try:
            res = requests.delete(f"{self.base_url}/admin/pdf/user/{userid}/file/{filename}", auth=self.auth)
            result = res.json()
            if "message" in result:
                print(f"✅ {result['message']}")
                if "deleted_files" in result and result["deleted_files"]:
                    print(f"   Files deleted: {result['deleted_files']}")
                if "deleted_from_db" in result and result["deleted_from_db"]:
                    print(f"   Database records deleted: {result['deleted_from_db']}")
                if "files_not_deleted" in result and result["files_not_deleted"]:
                    print(f"   Files not deleted (shared): {result['files_not_deleted']}")
            else:
                print(result)
        except Exception as e:
            print(f"Error: {e}")

    def show_menu(self):
        print("\n=== Admin PDF Data Management ===")
        print("    1. Upload PDF for user")
        print("    2. Upload PDF for everyone (global)")
        print("    3. Remove PDF from data by filename")
        print("    4. Remove all PDFs from data by userid")
        print("    5. Remove all PDFs from data (global)")
        print("    6. List all PDFs with users")
        print("    7. Ingest all PDFs for specific user")
        print("    8. Ingest specific PDF for user")
        print("    9. Upload ALL PDFs from folder for user")
        print("   10. Upload ALL PDFs from folder (global)")
        print("   11. Remove specific PDF by userid and filename")
        print("   12. Exit")
        choice = input("\nEnter your choice (1-12): ").strip()
        if choice == "1":
            self.upload_pdf_for_user()
        elif choice == "2":
            self.upload_pdf_global()
        elif choice == "3":
            self.remove_pdf_from_data_by_filename()
        elif choice == "4":
            self.remove_pdfs_from_data_by_userid()
        elif choice == "5":
            self.remove_all_pdfs_from_data()
        elif choice == "6":
            self.list_all_pdfs_with_users()
        elif choice == "7":
            self.ingest_pdfs_for_user()
        elif choice == "8":
            self.ingest_pdf_for_user()
        elif choice == "9":
            self.upload_all_pdfs_from_folder_for_user()
        elif choice == "10":
            self.upload_all_pdfs_from_folder_global()
        elif choice == "11":
            self.remove_pdf_by_userid_and_filename()
        elif choice == "12":
            print("Exiting...")
            return False
        else:
            print("Invalid choice. Please try again.")
        return True

if __name__ == "__main__":
    base_url = os.getenv("BASE_URL", "http://40.82.161.202:8000")
    admin_user = os.getenv("ADMIN_USER")
    admin_password = os.getenv("ADMIN_PASSWORD")

    if not admin_user or not admin_password:
        print("Admin credentials not found in .env file.")
        admin_user = input("Enter admin username: ").strip()
        admin_password = getpass.getpass("Enter admin password: ")

    # Assume DataManager is the class defined in this file
    manager = PDFDataManager(admin_user, admin_password, base_url)
    while True:
        if not manager.show_menu():
            break
