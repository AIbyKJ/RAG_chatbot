import os
import requests
from requests.auth import HTTPBasicAuth
import getpass

class MemoryManager:
    def __init__(self, username="", password="", base_url="http://127.0.0.1:8000"):
        self.username = username
        self.password = password
        self.base_url = base_url
        self.auth = HTTPBasicAuth(username, password)

    def clear_all_chat_history(self):
        res = requests.delete(f"{self.base_url}/vectordb/memory", auth=self.auth)
        if res.status_code == 200:
            print("✅", res.json().get("message", "Memory cleared for all users."))
        else:
            print("Error:", res.json().get("error", "Failed to clear all memory."))

    def clear_chat_history_by_user(self):
        try:
            res = requests.get(f"{self.base_url}/users", auth=self.auth)
            if res.status_code == 200:
                available_users = res.json().get("user_ids", [])
            else:
                print("Error fetching available users.")
                return

            if available_users:
                print("Available users with chat history:")
                for i, user in enumerate(available_users, 1):
                    print(f"{i}. {user}")
                print()
            else:
                print("No users with chat history found.")
                return
        except Exception as e:
            print(f"Error fetching available users: {e}")
            return
        user_id = input("Enter user ID to clear memory: ").strip()
        if not user_id:
            print("User ID cannot be empty.")
            return
        res = requests.delete(f"{self.base_url}/vectordb/memory/{user_id}", auth=self.auth)
        if res.status_code == 200:
            print("✅", res.json().get("message", "Memory cleared."))
        else:
            print("Error:", res.json().get("error", "Failed to clear memory."))

    def clear_all_pdf(self):
        res = requests.delete(f"{self.base_url}/vectordb/pdf", auth=self.auth)
        if res.status_code == 200:
            print("✅", res.json().get("message", "All PDF data cleared."))
        else:
            print("Error:", res.json().get("error", "Failed to clear PDF data."))

    def clear_pdf_by_name(self):
        try:
            res = requests.get(f"{self.base_url}/vectordb/pdf/sources", auth=self.auth)
            if res.status_code == 200:
                sources = res.json().get("sources", [])
                if sources:
                    print("Available PDF sources in vectordb:")
                    for i, source in enumerate(sources, 1):
                        print(f"{i}. {os.path.basename(source)}")
                    print()
                else:
                    print("No PDF sources found in vectordb.")
            else:
                print("Failed to fetch available PDF sources.")
        except Exception as e:
            print(f"Error fetching available PDF sources: {e}")
        source_name = input("Enter the file name of the PDF to clear (as shown above): ").strip()
        if not source_name:
            print("Source name cannot be empty.")
            return
        res = requests.delete(f"{self.base_url}/vectordb/pdf/{source_name}", auth=self.auth)
        if res.status_code == 200:
            print("✅", res.json().get("message", f"PDF data cleared for source {source_name}."))
        else:
            print("Error:", res.json().get("error", f"Failed to clear PDF data for source {source_name}."))

    def clear_all_vectordb_memory(self):
        self.clear_all_pdf()
        self.clear_all_chat_history()

    def list_available_users(self):
        res = requests.get(f"{self.base_url}/users", auth=self.auth)
        if res.status_code == 200:
            users = res.json().get("user_ids", [])
            if users:
                print("Available users:")
                for i, user in enumerate(users, 1):
                    print(f"{i}. {user}")
            else:
                print("No users found.")
        else:
            print("Error fetching users.")

    def list_pdfs_in_chroma(self):
        res = requests.get(f"{self.base_url}/vectordb/pdf/sources", auth=self.auth)
        if res.status_code == 200:
            sources = res.json().get("sources", [])
            if sources:
                print("Available PDFs in vectordb:")
                for i, source in enumerate(sources, 1):
                    print(f"{i}. {os.path.basename(source)}")
            else:
                print("No PDFs found in vectordb.")
        else:
            print("Error fetching PDFs from vectordb.")

    def ingest_pdf_for_users(self):
        pdf_paths = input("Enter PDF file paths to ingest (comma separated): ").split(",")
        pdf_paths = [p.strip() for p in pdf_paths if p.strip()]
        if not pdf_paths:
            print("No valid PDF files provided.")
            return
        user_list = input("Enter user IDs to associate (comma separated), or leave blank for everyone: ").strip()
        is_global = 0
        users = []
        if not user_list:
            is_global = 1
        else:
            users = [u.strip() for u in user_list.split(",") if u.strip()]
        files = [("files", (os.path.basename(path), open(path, "rb"), "application/pdf")) for path in pdf_paths if os.path.isfile(path)]
        if not files:
            print("No valid PDF files found.")
            return
        try:
            if is_global:
                res = requests.post(f"{self.base_url}/admin/pdf/upload", params={"is_global": 1}, files=files, auth=self.auth)
                for _, file_tuple in files:
                    file_tuple[1].close()
                print(res.json())
            else:
                for userid in users:
                    res = requests.post(f"{self.base_url}/admin/pdf/upload", params={"userid": userid, "is_global": 0}, files=files, auth=self.auth)
                    for _, file_tuple in files:
                        file_tuple[1].close()
                    print(f"For user {userid}: {res.json()}")
        except Exception as e:
            print(f"Error: {e}")



    def ingest_all_pdfs(self):
        res = requests.post(f"{self.base_url}/pdf/ingest", auth=self.auth)
        if res.status_code == 200:
            print("Ingested:", res.json())
        else:
            print("Error:", res.json().get("error", "Failed to ingest all PDFs."))

    def ingest_pdf_by_filename(self):
        res = requests.get(f"{self.base_url}/pdf", auth=self.auth)
        if res.status_code == 200:
            pdfs = res.json().get("pdfs", [])
            if pdfs:
                print("Available PDFs:")
                for i, pdf in enumerate(pdfs, 1):
                    print(f"{i}. {pdf}")
            else:
                print("No PDFs found.")
        else:
            print("Error fetching available PDFs.")
        filename = input("Enter PDF filename to ingest: ").strip()
        if not filename:
            print("Filename cannot be empty.")
            return
        res = requests.post(f"{self.base_url}/pdf/ingest/{filename}", auth=self.auth)
        if res.status_code == 200:
            print("Ingested:", res.json())
        else:
            print("Error:", res.json().get("error", f"Failed to ingest {filename}."))

    def remove_pdf_from_chroma_by_filename(self):
        filename = input("Enter PDF filename to remove from Chroma: ").strip()
        res = requests.delete(f"{self.base_url}/vectordb/pdf/{filename}", auth=self.auth)
        print(res.json())

    def remove_pdfs_from_chroma_by_userid(self):
        userid = input("Enter user ID to remove all their PDFs from Chroma: ").strip()
        res = requests.delete(f"{self.base_url}/vectordb/pdf/user/{userid}", auth=self.auth)
        result = res.json()
        if "message" in result:
            print(f"✅ {result['message']}")
            if "deleted_from_vectordb" in result and result["deleted_from_vectordb"]:
                print(f"   Vector embeddings deleted: {result['deleted_from_vectordb']}")
        else:
            print(result)

    def remove_all_pdfs_from_chroma(self):
        res = requests.delete(f"{self.base_url}/vectordb/pdf", auth=self.auth)
        print(res.json())

    def show_menu(self):
        print("\n=== Memory and PDF Management ===")
        print("    1. Clear chat history for all users")
        print("    2. Clear chat history for specific user")
        print("    3. Clear all PDF data from vectordb (ChromaDB)")
        print("    4. Clear PDF data by filename")
        print("    5. Clear all vectordb memory")
        print("    6. List available users")
        print("    7. List available PDFs in vectordb (ChromaDB)")
        print("    8. Remove PDF from Chroma by filename (admin)")
        print("    9. Remove all PDFs from Chroma by userid (admin)")
        print("   10. Remove all PDFs from Chroma (global, admin)")
        print("   11. Ingest PDF for users or everyone (admin)")
        print("   12. Ingest all PDFs (admin)")
        print("   13. Ingest PDF by filename (admin)")
        print("   14. Exit")
        choice = input("\nEnter your choice (1-14): ").strip()
        if choice == "1":
            self.clear_all_chat_history()
        elif choice == "2":
            self.clear_chat_history_by_user()
        elif choice == "3":
            self.clear_all_pdf()
        elif choice == "4":
            self.clear_pdf_by_name()
        elif choice == "5":
            self.clear_all_vectordb_memory()
        elif choice == "6":
            self.list_available_users()
        elif choice == "7":
            self.list_pdfs_in_chroma()
        elif choice == "8":
            self.remove_pdf_from_chroma_by_filename()
        elif choice == "9":
            self.remove_pdfs_from_chroma_by_userid()
        elif choice == "10":
            self.remove_all_pdfs_from_chroma()
        elif choice == "11":
            self.ingest_pdf_for_users()
        elif choice == "12":
            self.ingest_all_pdfs()
        elif choice == "13":
            self.ingest_pdf_by_filename()
        elif choice == "14":
            print("Exiting...")
            return False
        else:
            print("Invalid choice. Please try again.")
        return True

if __name__ == "__main__":
    # base_url = "http://127.0.0.1:8000"
    base_url = "http://40.82.161.202:8000"

    username = input("Enter username: ").strip()
    password = input("Enter password: ").strip()
    manager = MemoryManager(username, password, base_url)
    while True:
        if not manager.show_menu():
            break