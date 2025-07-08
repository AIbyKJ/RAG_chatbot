from clear_memory import show_menu as clear_memory_menu
from data_management import show_menu as data_management_menu

def main_menu():
    while True:
        print("\n=== Main Tools CLI ===")
        print("1. Memory Management")
        print("2. PDF Data Management")
        print("3. Exit")
        choice = input("Select an option (1-3): ").strip()
        if choice == "1":
            while True:
                if not clear_memory_menu():
                    break
        elif choice == "2":
            while True:
                if not data_management_menu():
                    break
        elif choice == "3":
            print("Exiting...")
            break
        else:
            print("Invalid choice.")

if __name__ == "__main__":
    main_menu()
