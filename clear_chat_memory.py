import requests

API = "http://127.0.0.1:8000/chat"
def clear_memory_by_user():
    user_id = input("Enter user ID to clear memory: ").strip()
    if not user_id:
        print("User ID cannot be empty.")
        return
    res = requests.delete(f"http://127.0.0.1:8000/memory/{user_id}")
    if res.status_code == 200:
        print(res.json().get("message", "Memory cleared."))
    else:
        print("Error:", res.json().get("error", "Failed to clear memory."))

def clear_all_memory():
    res = requests.delete("http://127.0.0.1:8000/memory")
    if res.status_code == 200:
        print(res.json().get("message", "All memory cleared."))
    else:
        print("Error:", res.json().get("error", "Failed to clear all memory."))

def clear_all_pdf():
    """Clear all PDF data from the database."""
    res = requests.delete("http://127.0.0.1:8000/pdf")
    if res.status_code == 200:
        print(res.json().get("message", "All PDF data cleared."))
    else:
        print("Error:", res.json().get("error", "Failed to clear PDF data."))

def clear_pdf_by_name():
    """Clear PDF data for a specific source name."""
    source_name = input("Enter PDF source name to clear: ").strip()
    if not source_name:
        print("Source name cannot be empty.")
        return
    
    res = requests.delete(f"http://127.0.0.1:8000/pdf/{source_name}")
    if res.status_code == 200:
        print(res.json().get("message", f"PDF data cleared for source {source_name}."))
    else:
        print("Error:", res.json().get("error", f"Failed to clear PDF data for source {source_name}."))

def show_menu():
    """Display menu options for memory and PDF clearing operations."""
    print("\n=== Memory and PDF Management ===")
    print("1. Clear memory for specific user")
    print("2. Clear all memory")
    print("3. Clear all PDF data")
    print("4. Clear PDF data by source name")
    print("5. Exit")
    
    choice = input("\nEnter your choice (1-5): ").strip()
    
    if choice == "1":
        clear_memory_by_user()
    elif choice == "2":
        clear_all_memory()
    elif choice == "3":
        clear_all_pdf()
    elif choice == "4":
        clear_pdf_by_name()
    elif choice == "5":
        print("Exiting...")
        return False
    else:
        print("Invalid choice. Please try again.")
    
    return True


if __name__ == "__main__":
    show_menu()