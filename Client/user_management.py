import os
import getpass
import requests
from requests.auth import HTTPBasicAuth

class UserManager:
    def __init__(self, username, password, base_url):
        self.username = username
        self.password = password
        self.base_url = base_url
        self.auth = HTTPBasicAuth(username, password)

    def add_user(self):
        userid = input("Enter new user ID: ").strip()
        password = getpass.getpass("Enter default password: ")
        is_admin = input("Is admin? (0/1): ").strip()
        try:
            res = requests.post(f"{self.base_url}/admin/user/add", json={"userid": userid, "password": password, "is_admin": int(is_admin)}, auth=self.auth)
            print(res.json())
        except Exception as e:
            print(f"Error: {e}")

    def delete_user(self):
        userid = input("Enter user ID to delete: ").strip()
        try:
            res = requests.delete(f"{self.base_url}/admin/user/delete", json={"userid": userid}, auth=self.auth)
            print(res.json())
        except Exception as e:
            print(f"Error: {e}")

    def list_users(self):
        try:
            res = requests.get(f"{self.base_url}/admin/users", auth=self.auth)
            if res.status_code == 200:
                users = res.json().get("users", [])
                if users:
                    print("Users in database:")
                    for i, user in enumerate(users, 1):
                        admin_status = " (Admin)" if user.get("is_admin") else ""
                        print(f"{i}. {user['userid']}{admin_status}")
                else:
                    print("No users found in database.")
            else:
                print("Error:", res.json().get("error", "Failed to fetch users."))
        except Exception as e:
            print(f"Error: {e}")

    def reset_user_password(self):
        userid = input("Enter user ID to reset password: ").strip()
        new_password = getpass.getpass("Enter new password: ")
        try:
            res = requests.post(
                f"{self.base_url}/admin/user/reset_password",
                json={"userid": userid, "new_password": new_password},
                auth=self.auth
            )
            print(res.json())
        except Exception as e:
            print(f"Error: {e}")

    def show_menu(self):
        print("\n=== User Management ===")
        print("    1. Add User")
        print("    2. Delete User")
        print("    3. List Users")
        print("    4. Reset User Password")
        print("    5. Back")
        choice = input("Select an option (1-5): ").strip()
        if choice == "1":
            self.add_user()
        elif choice == "2":
            self.delete_user()
        elif choice == "3":
            self.list_users()
        elif choice == "4":
            self.reset_user_password()
        elif choice == "5":
            return False
        else:
            print("Invalid choice.")
        return True

if __name__ == "__main__":
    base_url = os.getenv("BASE_URL", "http://40.82.161.202:8000")
    admin_user = os.getenv("ADMIN_USER")
    admin_password = os.getenv("ADMIN_PASSWORD")

    if not admin_user or not admin_password:
        print("Admin credentials not found in .env file.")
        admin_user = input("Enter admin username: ").strip()
        admin_password = getpass.getpass("Enter admin password: ")

    manager = UserManager(admin_user, admin_password, base_url)
    while True:
        if not manager.show_menu():
            break
