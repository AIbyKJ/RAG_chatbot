import getpass
import requests
from requests.auth import HTTPBasicAuth
from clear_memory import show_menu as clear_memory_menu, MemoryManager
from data_management import show_menu as data_management_menu, PDFDataManager

# BASE_URL = "http://127.0.0.1:8000"  # Should match your backend
BASE_URL = "http://40.82.161.202:8000"  # Should match your backend

class ToolsManager:
    def __init__(self, username="", password=""):
        self.memory_manager = MemoryManager(username, password, BASE_URL)
        self.pdf_manager = PDFDataManager(username, password, BASE_URL)

    def main_menu(self):
        while True:
            print("\n=== Main Tools CLI ===")
            print("    1. Memory Management")
            print("    2. PDF Data Management")
            print("    3. Exit")
            choice = input("Select an option (1-3): ").strip()
            if choice == "1":
                while True:
                    if not clear_memory_menu(self.memory_manager):
                        break
            elif choice == "2":
                while True:
                    if not data_management_menu(self.pdf_manager):
                        break
            elif choice == "3":
                print("Exiting...")
                break
            else:
                print("Invalid choice.")

def authenticate():
    print("=== Login Required ===")
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
    tools = ToolsManager(username, password)
    tools.main_menu()
