import getpass
import requests
from requests.auth import HTTPBasicAuth
from memory_management import MemoryManager
from data_management import PDFDataManager
from user_management import UserManager

BASE_URL = "http://127.0.0.1:8000"
# BASE_URL = "http://40.82.161.202:8000"

class AdminToolsManager:
    def __init__(self, username="", password=""):
        self.memory_manager = MemoryManager(username, password, BASE_URL)
        self.pdf_manager = PDFDataManager(username, password, BASE_URL)
        self.user_manager = UserManager(username, password, BASE_URL)
        self.username = username
        self.password = password
        self.auth = HTTPBasicAuth(username, password)

    def main_menu(self):
        while True:
            print("\n=== Admin Tools CLI ===")
            print("    1. User Management")
            print("    2. PDF Management")
            print("    3. Memory Management")
            print("    4. Exit")
            choice = input("Select an option (1-4): ").strip()
            if choice == "1":
                while True:
                    if not self.user_manager.show_menu():
                        break
            elif choice == "2":
                while True:
                    if not self.pdf_manager.show_menu():
                        break
            elif choice == "3":
                while True:
                    if not self.memory_manager.show_menu():
                        break
            elif choice == "4":
                print("Exiting...")
                break
            else:
                print("Invalid choice.")

def authenticate():
    print("=== Admin Login Required ===")
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
    tools = AdminToolsManager(username, password)
    tools.main_menu() 